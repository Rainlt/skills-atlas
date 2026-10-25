import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import atlas
import toolbox_index
from scripts import build_pages


class ToolboxTests(unittest.TestCase):
    def test_toolbox_query_does_not_load_the_full_skill_catalog(self):
        output = io.StringIO()
        with patch('sys.argv', ['atlas.py', 'toolboxes', '科研', '--json']), patch.object(atlas, 'catalog', side_effect=AssertionError('full catalog loaded')), contextlib.redirect_stdout(output):
            self.assertEqual(atlas.main(), 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result['results'][0]['id'], 'research-toolbox')
        self.assertEqual(result['results'][0]['access'], 'private')
        self.assertEqual(toolbox_index.find(atlas.ROOT, '无关领域任务')['results'], [])

    def test_archived_toolbox_keeps_history_but_exits_default_lookup(self):
        data = copy.deepcopy(toolbox_index.load(atlas.ROOT))
        data['toolboxes'] = data['toolboxes'][:1]
        row = data['toolboxes'][0]
        row.update(state='archived', reason='真实任务不适配；保留旧版本，等待替代组合。')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'toolboxes').mkdir()
            (root / 'toolboxes/index.json').write_text(json.dumps(data))
            self.assertEqual(toolbox_index.find(root, '科研')['results'], [])
            self.assertEqual(toolbox_index.find(root, '科研', include_archived=True)['results'][0]['reason'], row['reason'])

    def test_publish_rejects_stale_embedded_toolbox_index(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'data').mkdir()
            (root / 'toolboxes').mkdir()
            (root / 'browse.html').write_text('<script id="atlas-data" type="application/json">' + json.dumps({'snapshot': 's', 'skills': [], 'curation_version': 'c', 'toolboxes': []}) + '</script>')
            (root / 'data/catalog.json').write_text(json.dumps({'snapshot': 's', 'skills': []}))
            for name in ('curated', 'shortlist'):
                (root / ('data/' + name + '.json')).write_text(json.dumps({'curation_version': 'c'}))
            (root / 'toolboxes/index.json').write_text(json.dumps({'toolboxes': [{'id': 'new-toolbox'}]}))
            with patch.object(build_pages, 'ROOT', root), self.assertRaisesRegex(ValueError, '工具箱索引不一致'):
                build_pages.build(root / 'output')
            self.assertFalse((root / 'output').exists())


if __name__ == '__main__':
    unittest.main()
