"""Build compact editorial views; preserve original IDs, bundles and source evidence."""
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import re

LEVELS = {'unverified': ('尚未验证', 0), 'stale': ('版本变化，待复核', 0),
          'metadata_reviewed': ('用途与结构已核对', 1),
          'download_verified': ('下载已验证', 2), 'task_verified': ('任务已跑通', 3)}
STATES = {'catalog', 'featured', 'candidate', 'watch', 'archived'}


def normalized_name(name):
    return re.sub(r'[\s_]+', '-', name.strip().casefold())


def build(data, selection, manifests, signals=None, as_of='2026-10-25'):
    today = date.fromisoformat(as_of)
    policy = {'featured_limit': 40, 'review_days': 30, 'candidate_days': 30,
              'high_star_threshold': 10000, 'signals_max_age_days': 30, **selection.get('policy', {})}
    if len(selection['featured']) > policy['featured_limit']:
        raise ValueError('精选超出容量，请先合并或移出旧项')
    skills = data['skills']; by_id = {s['id']: s for s in skills}
    if len(by_id) != len(skills):
        raise ValueError('重复技能 ID')
    parents = {s['id']: s['id'] for s in skills}
    def find(key):
        while parents[key] != key:
            parents[key] = parents[parents[key]]; key = parents[key]
        return key
    def join(a, b):
        a, b = find(a), find(b); parents[max(a, b)] = min(a, b)
    names, instructions = {}, {}
    for s in skills:
        name = normalized_name(s['name'])
        if name in names: join(s['id'], names[name])
        names[name] = s['id']
        digest = s.get('instruction_sha256')
        if digest:
            if digest in instructions: join(s['id'], instructions[digest])
            instructions[digest] = s['id']
    for group in selection.get('groups', []):
        members = group['members']
        if not members or any(i not in by_id for i in members) or not group.get('reason'):
            raise ValueError('人工分组需要有效 ID 和理由')
        for member in members[1:]: join(members[0], member)
    entries, missing = {}, []
    for position, entry in enumerate(selection['featured']):
        if entry['id'] not in by_id:
            missing.append(entry['id']); continue
        gid = find(entry['id'])
        if gid in entries: raise ValueError('同一分组有多个精选入口: ' + entry['id'])
        entries[gid] = {**entry, 'position': position}
    source_map = {s['repo']: s for s in data.get('sources', [])}
    signals = signals or {'repositories': {}}
    featured_ids = {e['id'] for e in selection['featured']}
    slim, lifecycle_report = [], []
    for s in skills:
        loc = s['locations'][0]; record = selection.get('reviews', {}).get(s['id'])
        level, note = 'unverified', '尚无该固定版本的核对或运行记录。'
        if record:
            if record['level'] not in LEVELS or record['level'] in ('unverified', 'stale'):
                raise ValueError('无效的核对等级: ' + s['id'])
            if record['commit'] == loc['commit'] and record.get('bundle_sha') == loc['bundle_sha']:
                level, note = record['level'], record['note']
            else:
                level, note = 'stale', '上游版本或目录指纹变化，历史核对不能作为当前版本验证。'
        life = selection.get('lifecycle', {}).get(s['id'], {})
        state = life.get('state', 'featured' if s['id'] in featured_ids else 'catalog')
        if state not in STATES: raise ValueError('无效生命周期状态: ' + s['id'])
        reason = life.get('reason', '')
        if state in ('watch', 'archived') and not reason:
            raise ValueError('观察或归档必须说明原因: ' + s['id'])
        replaced_by = life.get('replaced_by')
        if replaced_by and (replaced_by not in by_id or replaced_by == s['id']):
            raise ValueError('替代项目必须指向其他现有 ID')
        if state == 'archived' and not life.get('changed_on'):
            raise ValueError('归档必须记录日期')
        deadline = life.get('next_review_at')
        if not deadline and state in ('featured', 'candidate'):
            start = life.get('entered_on') if state == 'candidate' else life.get('reviewed_on') or (record or {}).get('date')
            if start:
                deadline = (date.fromisoformat(start) + timedelta(days=policy['candidate_days'] if state == 'candidate' else policy['review_days'])).isoformat()
        if state == 'candidate' and not deadline:
            raise ValueError('候选需要观察期限')
        if state == 'featured' and (level in ('unverified', 'stale') or not deadline):
            state, reason = 'watch', '缺少当前版本的核对记录，退出精选等待复核。'
        if deadline and date.fromisoformat(deadline) <= today and state in ('featured', 'candidate'):
            state, reason = 'watch', '复查期限已到，退出精选或候选入口，等待复核；不据此判定失效。'
        if state in ('watch', 'archived'):
            lifecycle_report.append({'id': s['id'], 'state': state, 'reason': reason,
                                     'next_review_at': deadline, 'changed_on': life.get('changed_on'), 'replaced_by': replaced_by})
        origin = source_map.get(loc['repo'], {})
        repo_kind = 'collection' if origin.get('kind') == 'collection' else 'standalone' if origin.get('skills_scanned') == 1 else 'suite'
        signal = signals.get('repositories', {}).get(loc['repo'], {})
        captured = signal.get('captured_at')
        fresh = bool(captured and 0 <= (today - date.fromisoformat(captured[:10])).days <= policy['signals_max_age_days'])
        stars = signal.get('stars')
        if type(stars) is not int or stars < 0: stars = None
        repo_info = {'repo': loc['repo'], 'kind': repo_kind, 'stars': stars, 'captured_at': captured,
                     'fresh': fresh, 'high_star': bool(fresh and stars is not None and stars >= policy['high_star_threshold']),
                     'archived': signal.get('archived', origin.get('archived'))}
        integration = bool(re.search(r'rube\s+mcp|composio', (s['name'] + ' ' + s['description']).lower()))
        slim.append({'id': s['id'], 'name': s['name'], 'description': s['description'],
                     'categories': s['categories'], 'aliases': s['aliases'],
                     'sources': list(dict.fromkeys(x['repo'] for x in s['locations'])),
                     'url': loc['url'], 'commit': loc['commit'], 'license': loc['license'],
                     'external': s['has_external_refs'], 'risk': s['declared_risk'],
                     'compatibility': s['compatibility'], 'format_issues': s['format_issues'],
                     'group_id': find(s['id']), 'integration': integration,
                     'file_count': len(manifests.get(loc['bundle_sha'], [])), 'source_priority': loc['priority'],
                     'repository': repo_info, 'lifecycle': {'state': state, 'reason': reason,
                         'next_review_at': deadline, 'changed_on': life.get('changed_on'), 'replaced_by': replaced_by},
                     'verification': {'level': level, 'label': LEVELS[level][0], 'rank': LEVELS[level][1],
                                      'note': note, 'date': record.get('date') if record else None}})
    slim_map = {s['id']: s for s in slim}; buckets = {}
    for s in slim: buckets.setdefault(s['group_id'], []).append(s)
    groups = []
    for gid, members in sorted(buckets.items()):
        entry = entries.get(gid)
        preferred = entry['id'] if entry else min(members, key=lambda s: (
            -s['verification']['rank'], -int(s['repository']['kind'] == 'standalone'),
            s['source_priority'], s['id']))['id']
        featured = bool(entry and slim_map[preferred]['lifecycle']['state'] == 'featured')
        groups.append({'id': gid, 'members': sorted(s['id'] for s in members), 'preferred': preferred,
                       'title': entry['title'] if entry else slim_map[preferred]['name'],
                       'summary': entry['summary'] if entry else '', 'reason': entry['reason'] if entry else '',
                       'keywords': entry['keywords'] if entry else [], 'featured': featured,
                       'position': entry['position'] if entry else 10000,
                       'grouping_notes': [g['reason'] for g in selection.get('groups', []) if find(g['members'][0]) == gid],
                       'grouping': '用途入口' if entry else '同名或同说明候选，需比较适用条件'})
    version = hashlib.sha256(json.dumps({'selection': selection, 'signals': signals, 'as_of': as_of, 'snapshot': data['snapshot']},
                                        sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
    return {'schema_version': 1, 'snapshot': data['snapshot'], 'as_of': as_of, 'policy': policy,
            'skills': sorted(slim, key=lambda s: s['id']), 'groups': groups, 'curation_version': version,
            'curation': {'featured_groups': sum(g['featured'] for g in groups), 'all_groups': len(groups),
                         'merged_entries': len(skills)-len(groups), 'integration_skills': sum(s['integration'] for s in slim),
                         'missing_featured': missing, 'due_or_archived': len(lifecycle_report)},
            'lifecycle_report': lifecycle_report}


def generate(data, as_of=None):
    root = Path(__file__).resolve().parents[1]
    path = root / 'data/curated.json'
    if as_of is None:
        as_of = json.loads(path.read_text())['as_of'] if path.exists() else data['generated_at'][:10]
    signals_path = root / 'data/repository-signals.json'
    result = build(data, json.loads((root/'curation.json').read_text()),
                   json.loads((root/'data/manifests.json').read_text()),
                   json.loads(signals_path.read_text()) if signals_path.exists() else None, as_of)
    path.write_text(json.dumps(result, ensure_ascii=False, separators=(',', ':')) + '\n')
    selected = [g for g in result['groups'] if g['featured']]
    selected.sort(key=lambda g: g['position'])
    ids = {i for g in selected for i in g['members']}
    short = {**result, 'skills': [s for s in result['skills'] if s['id'] in ids], 'groups': selected, 'lifecycle_report': []}
    (root/'data/shortlist.json').write_text(json.dumps(short, ensure_ascii=False, separators=(',', ':')) + '\n')
    lines = ['# 精选技能速查', '', '供人和 AI 先查用途；未命中再扩展全库。核对等级与 Star 分开记录。', '',
             '| 用途 | 入口 ID | 核对状态 | 下次复查 |', '|---|---|---|---|']
    smap = {s['id']: s for s in result['skills']}
    for g in selected:
        s = smap[g['preferred']]
        lines.append('| {} | `{}` | {} | {} |'.format(g['title'], s['id'], s['verification']['label'], s['lifecycle']['next_review_at']))
    (root/'SHORTLIST.md').write_text('\n'.join(lines)+'\n')
    (root/'data/lifecycle-report.json').write_text(json.dumps({'as_of': as_of, 'missing_featured': result['curation']['missing_featured'],
                        'items': result['lifecycle_report']}, ensure_ascii=False, indent=2)+'\n')
    return result
