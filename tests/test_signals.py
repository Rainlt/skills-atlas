import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import refresh_signals


class RepositorySignalTests(unittest.TestCase):
    def test_failure_preserves_count_and_capture_date(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'data').mkdir()
            (root/'sources.json').write_text(json.dumps({'sources':[{'repo':'owner/tool'}]}))
            old={'stars':12000,'captured_at':'2026-01-01T00:00:00Z','archived':False}
            (root/'data/repository-signals.json').write_text(json.dumps({'repositories':{'owner/tool':old}}))
            with patch.object(refresh_signals,'ROOT',root),patch.object(refresh_signals.atlas,'api',side_effect=OSError('offline')):
                result=refresh_signals.refresh()
            self.assertEqual(result['repositories']['owner/tool'],old)
            self.assertEqual(len(result['errors']),1)
    def test_missing_or_invalid_count_is_not_zero_or_fresh(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'data').mkdir();(root/'sources.json').write_text(json.dumps({'sources':[{'repo':'owner/tool'}]}))
            with patch.object(refresh_signals,'ROOT',root),patch.object(refresh_signals.atlas,'api',return_value={'stargazers_count':None}):
                result=refresh_signals.refresh()
            self.assertNotIn('owner/tool',result['repositories']);self.assertEqual(len(result['errors']),1)
