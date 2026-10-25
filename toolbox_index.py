"""Lightweight public toolbox pointers; canonical instructions remain at source."""
import json
import re
from pathlib import Path
from urllib.parse import urlparse


def load(root):
    data = json.loads((Path(root) / 'toolboxes/index.json').read_text(encoding='utf-8'))
    if data.get('schema_version') != 1 or not isinstance(data.get('toolboxes'), list):
        raise ValueError('工具箱索引版本或结构无效')
    seen = set()
    for item in data['toolboxes']:
        key = item['id']
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', key) or key in seen:
            raise ValueError('工具箱 ID 无效或重复：' + key)
        seen.add(key)
        for field in ('name', 'summary', 'example', 'verification', 'checked_on', 'reason', 'invoke', 'canonical_version'):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError('工具箱缺少字段：' + field)
        for field in ('stages', 'helpers', 'keywords'):
            if not isinstance(item.get(field), list) or not item[field] or any(not isinstance(s, str) or not s.strip() for s in item[field]):
                raise ValueError('工具箱列表无效：' + field)
        if item.get('state') not in ('active', 'watch', 'archived') or item.get('access') not in ('public', 'private'):
            raise ValueError('工具箱状态或访问级别无效')
        if not re.fullmatch(r'[0-9a-f]{40}', item.get('canonical_commit', '')):
            raise ValueError('工具箱缺少核对版本')
        for field in ('guide_url', 'entry_url'):
            url = urlparse(item.get(field, ''))
            if url.scheme != 'https' or url.netloc != 'github.com' or not url.path.startswith('/Rainlt/methods-atlas/'):
                raise ValueError('工具箱正文入口无效')
        if item.get('primary_count') != len(item['stages']) or item.get('component_count', 0) < item['primary_count']:
            raise ValueError('工具箱环节与组件数量不一致')
    return data


def find(root, query='', include_archived=False, limit=3):
    rows = load(root)['toolboxes']
    terms = query.casefold().split()
    results = []
    for item in rows:
        if item['state'] == 'archived' and not include_archived:
            continue
        text = ' '.join([item['id'], item['name'], item['summary'], *item['keywords'], *item['stages']]).casefold()
        if all(term in text for term in terms):
            results.append(item)
    return {'scope': 'toolboxes', 'total_matches': len(results), 'results': results[:max(1, limit)],
            'next': '先读选中工具箱的唯一正文；私有入口需仓库访问权限，查到入口不表示已安装。'}


def markdown(data):
    lines = ['# 工具箱 · 从技能库提炼的工作线', '',
             '按要完成的任务组织一套互补技能，同用途只选一个默认项；已有材料时从中途进入，按当前环节调用。', '',
             '[在线工具箱板块](https://rainlt.github.io/skills-atlas/#toolboxes) · [机器索引](index.json) · [返回技能库](../README.md)', '',
             '| 工具箱 | 能完成什么 / 例子 | 工作线 | 状态 |', '|---|---|---|---|']
    for t in data['toolboxes']:
        lines.append('| [{}]({}) | {} 例如：{} | {} | {}；{} |'.format(
            t['name'], t['guide_url'], t['summary'], t['example'], ' → '.join(t['stages']), t['state'], t['verification']))
    lines += ['', '## 调用与维护', '',
              '- 多环节任务先找工具箱：`python3 atlas.py toolboxes 科研 --json`，默认最多返回 3 项；再读所选入口，不加载全部底层技能。单项任务仍可直接查技能。',
              '- 本板块维护摘要、已核对版本与正文链接。正文统一在个人方法库 `Rainlt/methods-atlas`，目前为私有，需登录有权限的账号；不把本机安装状态推广到其他机器。',
              '- 科研工具箱的引用核查、绘图与中文清理按需使用；六环节共用来源、证据和结果，原九个组件保留。',
              '- 后续工具箱按任务新增一张卡片；默认组件冲突时先比较替换，不持续堆叠。同一正文只维护一份。',
              '- 版本变化、依赖失效或实际不适配时复核；待复核标为 watch，退出标为 archived 并保留原因与替代入口，不因低 Star、无反馈或短期未更新直接删除。',
              '- 此索引不增加单项技能数量或占用精选名额；不执行上游内容，也不自动安装整个工具箱。', '']
    return '\n'.join(lines)
