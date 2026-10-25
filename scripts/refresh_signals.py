#!/usr/bin/env python3
"""Refresh optional repository popularity signals; never treat stars as skill quality."""
import concurrent.futures
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import atlas
ROOT = atlas.ROOT


def refresh():
    path = ROOT / 'data/repository-signals.json'
    previous = json.loads(path.read_text()) if path.exists() else {'repositories': {}}
    sources = json.loads((ROOT / 'sources.json').read_text())['sources']
    now = datetime.now(timezone.utc).isoformat()
    records, errors = {}, []
    def get(source):
        repo = source['repo']
        try:
            meta = atlas.api('repos/' + repo)
            stars = meta.get('stargazers_count')
            if type(stars) is not int or stars < 0:
                raise ValueError('invalid repository star count')
            return repo, {'stars': stars, 'captured_at': now, 'archived': meta['archived'],
                          'pushed_at': meta.get('pushed_at'), 'url': meta['html_url']}, None
        except Exception as exc:
            return repo, previous['repositories'].get(repo), type(exc).__name__
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for repo, value, error in pool.map(get, sources):
            if value is not None:
                records[repo] = value
            if error:
                errors.append({'repo': repo, 'error': error})
    result = {'schema_version': 1, 'repositories': records, 'errors': errors}
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print('Repository signals: {} available, {} refresh failures; prior dates retained on failure.'.format(len(records), len(errors)))
    return result


if __name__ == '__main__':
    refresh()
