#!/usr/bin/env python3
"""Discover repositories independently of the source allowlist; never install them."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path, PurePosixPath
import re
import sys
import urllib.parse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import atlas
from scripts.update import frontmatter, markdown_cell

ROOT = atlas.ROOT


def merge_queue(previous, incoming, configured=(), excluded=()):
    """Retain inspection evidence and all discovery origins, including old README rows."""
    merged = {}
    excluded = {r.lower() for r in excluded}
    for item in [*previous, *incoming]:
        repo = item['repo']
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
            continue
        key = repo.lower()
        if key in excluded:
            continue
        old = merged.get(key, {})
        origins = set(old.get('origins', [])) | set(item.get('origins', []))
        if item.get('discovered_in'):
            origins.add('collection:' + item['discovered_in'])
        # A newly seen link must not erase a completed inspection.
        row = {**old, **{k: v for k, v in item.items() if k != 'status' or not old.get('checked_at')}}
        row['origins'] = sorted(origins)
        merged[key] = row
    configured = {r.lower() for r in configured}
    for key, row in merged.items():
        if key in configured:
            row['status'] = 'indexed'
    return sorted(merged.values(), key=lambda r: r['repo'].lower())


def search_candidates(config, configured, api=atlas.api):
    searches, groups = [], []
    configured = {r.lower() for r in configured}
    configured.update(r.lower() for r in config.get('excluded_repositories', []))
    for query in config['queries']:
        response = api('search/repositories?' + urllib.parse.urlencode({
            'q': query, 'sort': 'stars', 'order': 'desc', 'per_page': config['results_per_query']}))
        if response.get('incomplete_results') or 'items' not in response:
            raise ValueError('检索结果不完整: ' + query)
        items = response['items']
        searches.append({'query': query, 'total_count': response['total_count'],
                         'returned': len(items), 'results': [x['full_name'] for x in items]})
        groups.append([{'repo': x['full_name'], 'stars': x.get('stargazers_count', 0),
                        'origins': ['search:' + query], 'status': 'unverified_reference'}
                       for x in items if x['full_name'].lower() not in configured])
    # Give each query a turn; a broad topic cannot consume the entire inspection budget.
    ordered = []
    seen = set()
    for rank in range(max((len(g) for g in groups), default=0)):
        for group in groups:
            if rank < len(group) and group[rank]['repo'].lower() not in seen:
                ordered.append(group[rank]['repo'])
                seen.add(group[rank]['repo'].lower())
    return searches, merge_queue([], [r for g in groups for r in g]), ordered


def inspect_repository(repo, sample_count=3, api=atlas.api, fetch=atlas.fetch):
    meta = api('repos/' + repo)
    canonical = meta['full_name']
    if meta.get('archived'):
        return {'canonical_repo': canonical, 'status': 'archived'}
    commit = api('repos/' + canonical + '/commits/HEAD')
    sha = commit['sha']
    tree = api('repos/' + canonical + '/git/trees/' + commit['commit']['tree']['sha'] + '?recursive=1')
    if tree.get('truncated'):
        raise ValueError('目录树不完整，不能确认技能清单')
    items = {i['path']: i for i in tree['tree'] if i['type'] == 'blob' and i.get('mode') in ('100644', '100755')}
    paths = sorted((p for p in items if PurePosixPath(p).name == 'SKILL.md'),
                   key=lambda p: (not p.startswith('skills/'), p))
    samples = []
    for path in paths[:sample_count]:
        atlas.safe_relative(path)
        data = fetch(atlas.raw_url(canonical, sha, path))
        if atlas.blob_sha(data) != items[path]['sha']:
            raise ValueError('技能说明指纹不一致: ' + path)
        metadata, body, issue = frontmatter(data.decode('utf-8', errors='replace'))
        samples.append({'path': path, 'blob_sha': items[path]['sha'],
                        'name': str(metadata.get('name', '')), 'description': str(metadata.get('description', '')),
                        'frontmatter_issue': issue,
                        'external_references': bool(re.search(r'\.\./|\$\{?(?:CLAUDE_PLUGIN_ROOT|CODEX_HOME|SKILL_ROOT)', body))})
    valid = any(not s['frontmatter_issue'] and s['name'] and s['description'] for s in samples)
    return {'canonical_repo': canonical, 'status': 'verified_candidate' if valid else 'needs_review' if paths else 'no_skill_files',
            'commit': sha, 'repository_license': (meta.get('license') or {}).get('spdx_id', 'UNKNOWN'),
            'skill_paths': paths, 'samples': samples,
            'scope': '完整目录树与有限说明抽样；未执行、安装或验证运行兼容性'}


def run(config, previous, configured, api=atlas.api, fetch=atlas.fetch):
    # Complete every search first. A failed search cannot be published as a successful run.
    searches, incoming, order = search_candidates(config, configured, api)
    queue = merge_queue(previous, incoming, configured, config.get('excluded_repositories', []))
    by_repo = {r['repo'].lower(): r for r in queue}
    indexed = {r.lower() for r in configured}
    selected = order[:config['search_inspections']]
    chosen = {r.lower() for r in selected}
    # Revisit the oldest checked queue entries, rather than leaving a permanent static backlog.
    backlog = sorted((r for r in queue if r['repo'].lower() not in chosen | indexed),
                     key=lambda r: (r.get('checked_at', ''), r['repo'].lower()))
    selected += [r['repo'] for r in backlog[:config['queue_inspections']]]
    now = datetime.now(timezone.utc).isoformat()
    errors = []
    for repo in selected:
        row = by_repo[repo.lower()]
        print('核实候选 ' + repo, flush=True)
        try:
            result = inspect_repository(repo, config['skill_samples'], api, fetch)
            row.update(result)
            row['checked_at'] = now
            row.pop('last_error', None)
        except Exception as exc:
            # Retain prior positive evidence but do not label an unsuccessful recheck as verified.
            row['status'] = 'inspection_error'
            row['checked_at'] = now
            row['last_error'] = type(exc).__name__ + ': ' + str(exc)
            errors.append({'repo': repo, 'error': row['last_error']})
            print('  核实失败：' + row['last_error'], flush=True)
    return queue, {'schema_version': 1, 'checked_at': now, 'status': 'partial' if errors else 'complete',
                   'searches': searches, 'inspected': selected, 'errors': errors,
                   'limits': {k: v for k, v in config.items() if k != 'queries'},
                   'scope': '按检索式、排序和预算抽样，不代表覆盖全部 GitHub'}


def render(queue, report):
    rows = ['# 新来源发现', '',
            '候选来自独立 GitHub 搜索和已有合集链接。verified_candidate 仅表示已发现实际技能目录并校验部分说明，收录和依赖仍需审核。', '',
            '本次状态：`' + report['status'] + '`；检查时间：' + report['checked_at'], '',
            '## 本次检索', '', '| 查询 | 匹配总数 | 本次读取 |', '|---|---:|---:|']
    for s in report['searches']:
        rows.append('| {} | {} | {} |'.format(markdown_cell(s['query']), s['total_count'], s['returned']))
    rows += ['', '## 本次核实', '', '| 仓库 | 状态 | 技能文件数 | 证据 |', '|---|---|---:|---|']
    by_repo = {r['repo'].lower(): r for r in queue}
    for repo in report['inspected']:
        r = by_repo[repo.lower()]
        url = 'https://github.com/' + r.get('canonical_repo', repo)
        if r.get('commit'):
            url += '/tree/' + r['commit']
        rows.append('| [{}]({}) | {} | {} | {} |'.format(repo, url, r['status'], len(r.get('skill_paths', [])),
                    markdown_cell(r.get('last_error') or ', '.join(s['path'] for s in r.get('samples', [])))))
    rows += ['', '完整来源、命中查询、固定 commit、文件指纹和依赖线索见 `data/discovery-queue.json`；本次排名及错误见 `data/discovery-report.json`。', '',
             '审核通过后修改 `sources.json`，再更新索引。候选不会自动安装，也不会自动进入可下载目录。', '']
    return '\n'.join(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-repo', help='验收：要求本次独立搜索命中并成功核实该仓库；不会将它注入搜索')
    args = parser.parse_args()
    config = json.loads((ROOT / 'discovery.json').read_text())
    if (not config['queries'] or len(config['queries']) > 12
            or not 1 <= config['results_per_query'] <= 100 or not 1 <= config['skill_samples'] <= 10
            or not 1 <= config['search_inspections'] <= 60 or not 0 <= config['queue_inspections'] <= 20):
        raise ValueError('检索或抽样预算超出范围')
    configured = [s['repo'] for s in json.loads((ROOT / 'sources.json').read_text())['sources']]
    previous = json.loads((ROOT / 'data/discovery-queue.json').read_text())
    queue, report = run(config, previous, configured)
    # Check against this run, not against a stale previous positive result.
    accepted = not args.require_repo or any(r['repo'].lower() == args.require_repo.lower()
        and r['repo'] in report['inspected'] and r['status'] == 'verified_candidate'
        and any(r['repo'] in s['results'] for s in report['searches']) for r in queue)
    report['acceptance'] = {'required_repo': args.require_repo, 'passed': accepted} if args.require_repo else None
    for path, value in [('data/discovery-queue.json', queue), ('data/discovery-report.json', report)]:
        (ROOT / path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'docs/DISCOVERY.md').write_text(render(queue, report))
    print('发现流程：' + report['status'] + '；验收：' + str(accepted))
    return 0 if report['status'] == 'complete' and accepted else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('发现流程失败，未覆盖上次报告：' + type(exc).__name__ + ': ' + str(exc), file=sys.stderr)
        sys.exit(1)
