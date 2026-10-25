"""Standard-library search model for compact, grouped recommendations."""
import json
from pathlib import Path


def relevance(skill, group, terms, categories):
    name, identifier = skill['name'].lower(), skill['id'].lower()
    editorial = ' '.join([group['title'], group['summary'], *group['keywords']]).lower()
    names = {c['id']: c['name_zh'] for c in categories}
    text = ' '.join([identifier, name, skill['description'], *skill['categories'],
                     *(names.get(c, c) for c in skill['categories']), editorial]).lower()
    score = 0
    for t in terms:
        if t in (name, identifier): score += 100
        elif t in name: score += 40
        elif t in group['title'].lower(): score += 35
        elif t in editorial: score += 25
        elif t in identifier: score += 20
        elif t in text: score += 8
        else:
            expansion = [v.lower() for c in categories if t in c['queries_zh'] or t == c['name_zh'] for v in [c['id'], *c['keywords']]]
            if not any(v in text for v in expansion): return -1
            score += 1
    return score


def rank(skill):
    r = skill['repository']
    return (-skill['verification']['rank'], -int(r['kind'] == 'standalone'), -int(r['high_star']),
            -int(bool(skill['compatibility'] and not skill['compatibility'].startswith('未验证'))),
            -int(skill['file_count'] > 1), skill['source_priority'], skill['id'])


def filter_catalog(data, categories, query='', category='', source='', scope='featured', grouped=True, sort='relevance', include_archived=False):
    by_id = {s['id']: s for s in data['skills']}
    terms = query.lower().strip().split(); cards = []; matched = 0
    for group in data['groups']:
        if scope == 'featured' and not group['featured']: continue
        candidates = []
        for identifier in group['members']:
            s = by_id[identifier]; state = s['lifecycle']['state']
            if scope == 'archived':
                if state not in ('watch', 'archived'): continue
            elif not include_archived and state == 'archived': continue
            if scope == 'research' and not ('research' in s['categories'] or 'data' in s['categories'] or 'documents' in s['categories']): continue
            if scope == 'integrations' and not s['integration']: continue
            if category and category not in s['categories']: continue
            if source and not any(source.lower() in r.lower() for r in s['sources']): continue
            score = relevance(s, group, terms, categories)
            if score >= 0: candidates.append((s, score))
        def candidate_order(x):
            base = (-x[1], int(x[0]['lifecycle']['state'] == 'watch'), rank(x[0])[0], -int(x[0]['id'] == group['preferred']), *rank(x[0])[1:])
            r = x[0]['repository']
            return (-(r['stars'] if r['fresh'] and r['stars'] is not None else -1), *base) if sort == 'stars' else base
        candidates.sort(key=candidate_order)
        matched += len(candidates)
        if grouped and candidates:
            cards.append({'group': group, 'representative': candidates[0][0], 'variants': [s for s, _ in candidates], 'score': candidates[0][1]})
        elif not grouped:
            cards.extend({'group': group, 'representative': s, 'variants': [s], 'score': score} for s, score in candidates)
    def order(card):
        s = card['representative']; g = card['group']; stars = s['repository']['stars'] if s['repository']['fresh'] else None
        if sort == 'stars': return (-(stars if stars is not None else -1), -card['score'], *rank(s))
        if sort == 'name': return (s['name'].lower(), s['id'])
        return (-card['score'], -int(g['featured']), int(s['lifecycle']['state'] == 'watch'), rank(s)[0], -int(s['repository']['kind'] == 'standalone'),
                g['position'], *rank(s)[2:])
    cards.sort(key=order)
    return {'cards': cards, 'matched_skills': matched}


def compact(card):
    s, g = card['representative'], card['group']
    r = s['repository']
    return {'id': s['id'], 'task': g['title'] if s['id'] == g['preferred'] else s['name'],
            'summary': (g['summary'] if s['id'] == g['preferred'] else '') or s['description'][:220],
            'source': r['repo'], 'repository_kind': r['kind'], 'repository_stars': r['stars'],
            'stars_as_of': r['captured_at'], 'stars_fresh': r['fresh'],
            'verification': s['verification']['label'], 'state': s['lifecycle']['state'],
            'exit_reason': s['lifecycle']['reason'] or None, 'replacement': s['lifecycle']['replaced_by'],
            'alternatives': max(0, len(card['variants'])-1)}


def recommend(root, query='', category='', source='', limit=5, scope='auto', include_archived=False):
    root = Path(root)
    categories = json.loads((root/'taxonomy.json').read_text())['categories']
    short = json.loads((root/'data/shortlist.json').read_text())
    scope_used = 'featured' if scope == 'auto' else scope
    data = short if scope_used == 'featured' else json.loads((root/'data/curated.json').read_text())
    result = filter_catalog(data, categories, query, category, source, scope_used, include_archived=include_archived)
    fallback = False
    if scope == 'auto' and not result['cards']:
        scope_used, fallback = 'all', True
        data = json.loads((root/'data/curated.json').read_text())
        result = filter_catalog(data, categories, query, category, source, 'all', include_archived=include_archived)
    return {'scope': scope_used, 'expanded_to_all': fallback, 'total_groups': len(result['cards']),
            'results': [compact(c) for c in result['cards'][:limit]]}
