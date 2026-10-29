import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('pinned_update', Path(__file__).resolve().parents[1] / 'scripts/update.py')
update = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update)


class SourcePinTests(unittest.TestCase):
    def test_malformed_pin_rejected_before_fetch(self):
        with patch.object(update.subprocess, 'check_output') as fetch:
            with self.assertRaises(ValueError): update.git_snapshot('owner/repo', pinned_commit='main')
            fetch.assert_not_called()

    def test_fetch_uses_exact_pin_and_rejects_mismatch(self):
        pin = '1' * 40
        with tempfile.TemporaryDirectory() as temp, patch.object(update, 'CACHE', Path(temp)), \
             patch.object(update.subprocess, 'run'), \
             patch.object(update.subprocess, 'check_output', side_effect=[b'', b'2' * 40]) as call:
            with self.assertRaises(ValueError): update.git_snapshot('owner/repo', pinned_commit=pin)
            self.assertEqual(call.call_args_list[0].args[0][-1], pin)

    def test_offline_pin_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(update, 'CACHE', Path(temp)):
            source = Path(temp) / 'sources/owner--repo.json'; source.parent.mkdir()
            source.write_text(json.dumps({'commit': '2' * 40}))
            with self.assertRaises(ValueError):
                update.scan_source({'repo': 'owner/repo', 'pinned_commit': '1' * 40}, [], offline=True)
