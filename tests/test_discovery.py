import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import atlas
from scripts import discover


class DiscoveryTests(unittest.TestCase):
    def config(self):
        return {'queries': ['topic:agent-skills', '"long-horizon" agent in:name,description'],
                'results_per_query': 20, 'search_inspections': 2, 'queue_inspections': 1, 'skill_samples': 1}

    def fixture(self, name='sample-tool'):
        payload = ('---\nname: ' + name + '\ndescription: Durable goals\n---\nSee ../shared/guide.md').encode()
        items = [{'path': 'skills/sample/SKILL.md', 'sha': atlas.blob_sha(payload), 'type': 'blob', 'mode': '100644'}]
        def api(path):
            if path.startswith('search/'):
                repo = 'new/durable' if 'long-horizon' in path else 'popular/catalog'
                return {'total_count': 1, 'incomplete_results': False,
                        'items': [{'full_name': repo, 'stargazers_count': 100}]}
            if '/commits/' in path:
                return {'sha': '1' * 40, 'commit': {'tree': {'sha': '2' * 40}}}
            if '/git/trees/' in path:
                return {'tree': items, 'truncated': False}
            return {'full_name': path.removeprefix('repos/'), 'archived': False, 'license': {'spdx_id': 'MIT'}}
        return api, payload

    def test_independent_search_verifies_unseeded_repository_and_drains_queue(self):
        api, payload = self.fixture()
        previous = [{'repo': 'queue/oldest', 'discovered_in': 'collection/seed', 'status': 'unverified_reference'}]
        queue, report = discover.run(self.config(), previous, [], api, lambda u: payload)
        found = next(r for r in queue if r['repo'] == 'new/durable')
        self.assertEqual(found['status'], 'verified_candidate')
        self.assertEqual(found['commit'], '1' * 40)
        self.assertTrue(found['samples'][0]['external_references'])
        self.assertIn('queue/oldest', report['inspected'])
        self.assertEqual(report['status'], 'complete')

    def test_round_robin_keeps_specialist_query_in_budget(self):
        def api(path):
            prefix = 'specialist' if 'long-horizon' in path else 'general'
            return {'total_count': 20, 'items': [{'full_name': prefix + '/r' + str(i)} for i in range(20)]}
        _, _, order = discover.search_candidates(self.config(), [], api)
        self.assertEqual(order[:2], ['general/r0', 'specialist/r0'])

    def test_truncated_tree_and_tampering_never_verify(self):
        api, payload = self.fixture()
        with self.assertRaises(ValueError):
            discover.inspect_repository('new/durable', api=lambda p: {'truncated': True} if '/git/trees/' in p else api(p))
        with self.assertRaises(ValueError):
            discover.inspect_repository('new/durable', api=api, fetch=lambda u: b'tampered')

    def test_incomplete_search_fails_instead_of_false_coverage(self):
        with self.assertRaises(ValueError):
            discover.run(self.config(), [], [], api=lambda p: {'incomplete_results': True})

    def test_failed_inspection_is_partial_and_keeps_prior_evidence(self):
        api, payload = self.fixture()
        previous = [{'repo': 'new/durable', 'status': 'verified_candidate', 'commit': 'old', 'checked_at': 'old'}]
        queue, report = discover.run(self.config(), previous, [], api, lambda u: b'wrong')
        self.assertEqual(report['status'], 'partial')
        row = next(r for r in queue if r['repo'] == 'new/durable')
        self.assertEqual(row['status'], 'inspection_error')
        self.assertEqual(row['commit'], 'old')

    def test_merge_preserves_evidence_and_combines_origins_case_insensitively(self):
        rows = discover.merge_queue(
            [{'repo': 'New/Tool', 'status': 'verified_candidate', 'checked_at': 'yesterday',
              'commit': 'pinned', 'origins': ['search:agent']}],
            [{'repo': 'new/tool', 'discovered_in': 'collection/seed', 'status': 'unverified_reference'}])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['status'], 'verified_candidate')
        self.assertEqual(rows[0]['commit'], 'pinned')
        self.assertEqual(rows[0]['origins'], ['collection:collection/seed', 'search:agent'])
        self.assertEqual(discover.merge_queue(rows, [], ['NEW/TOOL'])[0]['status'], 'indexed')

    def test_no_skill_files_is_distinct_from_valid_skill(self):
        api, payload = self.fixture()
        row = discover.inspect_repository('new/durable',
            api=lambda p: {'tree': [], 'truncated': False} if '/git/trees/' in p else api(p), fetch=lambda u: payload)
        self.assertEqual(row['status'], 'no_skill_files')

    def test_explicit_exclusions_skip_search_and_old_queue_inspections(self):
        api, payload = self.fixture()
        config = {**self.config(), 'excluded_repositories': ['POPULAR/CATALOG', 'queue/oldest']}
        queue, report = discover.run(config, [{'repo': 'queue/oldest', 'status': 'verified_candidate'}],
                                     [], api, lambda url: payload)
        self.assertEqual([row['repo'] for row in queue], ['new/durable'])
        self.assertEqual(report['inspected'], ['new/durable'])

    def test_collection_links_cannot_restore_an_excluded_source(self):
        rows = discover.merge_queue([{'repo': 'removed/tool', 'status': 'indexed'}],
            [{'repo': 'REMOVED/tool', 'discovered_in': 'collection/seed'}], excluded=['Removed/Tool'])
        self.assertEqual(rows, [])

    def test_unsafe_yaml_does_not_become_verified_candidate(self):
        api, _ = self.fixture()
        payload = b"---\nname: !!python/object/apply:os.system ['echo unsafe']\n---\nbody"
        def bad_yaml_tree(path):
            if '/git/trees/' in path:
                return {'truncated': False, 'tree': [{'path': 'SKILL.md', 'sha': atlas.blob_sha(payload),
                         'type': 'blob', 'mode': '100644'}]}
            return api(path)
        row = discover.inspect_repository('new/durable', api=bad_yaml_tree, fetch=lambda u: payload)
        self.assertEqual(row['status'], 'needs_review')

    def test_failed_search_preserves_published_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'data').mkdir()
            (root / 'docs').mkdir()
            (root / 'discovery.json').write_text(json.dumps(self.config()))
            (root / 'sources.json').write_text('{"sources": []}')
            (root / 'data/discovery-queue.json').write_text('[]')
            (root / 'data/discovery-report.json').write_text('previous report')
            (root / 'docs/DISCOVERY.md').write_text('previous readable report')
            with patch.object(discover, 'ROOT', root), patch.object(discover, 'run', side_effect=ValueError('search failed')), \
                 patch.object(sys, 'argv', ['discover.py']):
                with self.assertRaises(ValueError):
                    discover.main()
            self.assertEqual((root / 'data/discovery-report.json').read_text(), 'previous report')
            self.assertEqual((root / 'docs/DISCOVERY.md').read_text(), 'previous readable report')


if __name__ == '__main__':
    unittest.main()
