import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import urllib.error
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import atlas


class DownloadTests(unittest.TestCase):
    def test_unsafe_paths(self):
        for path in ("../escape", "/absolute", "a/../escape", "a\\b", "a//b", "a/./b", ".git/config", "CON", "a/NUL.txt", "C:/windows"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                atlas.safe_relative(path)

    def fixture(self, root):
        payload = b"---\nname: demo\ndescription: fixture\n---\n# Demo\n"
        manifest = [{"path": "SKILL.md", "sha": atlas.blob_sha(payload), "mode": "100644", "type": "blob"}]
        sha = atlas.manifest_tree_sha(manifest)
        (root / "data").mkdir()
        (root / "data/manifests.json").write_text(json.dumps({sha: manifest}))
        loc = {"repo": "example/repo", "path": "skills/demo", "commit": "1" * 40,
               "bundle_sha": sha, "skill_sha": manifest[0]["sha"], "url": "https://github.com/example/repo", "license": {}, "notices": []}
        return {"id": "example/repo/skills/demo", "name": "demo", "locations": [loc], "has_external_refs": False}, payload

    def test_verified_download_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill, data = self.fixture(root)
            dest = root / "result"
            with patch.object(atlas, "ROOT", root), patch.object(atlas, "fetch", return_value=data):
                atlas.download(skill, dest)
                self.assertEqual((dest / "SKILL.md").read_bytes(), data)
                self.assertTrue((dest / ".atlas-receipt.json").exists())
                with self.assertRaises(ValueError):
                    atlas.download(skill, dest)

    def test_corruption_publishes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill, _ = self.fixture(root)
            dest = root / "result"
            with patch.object(atlas, "ROOT", root), patch.object(atlas, "fetch", return_value=b"tampered"):
                with self.assertRaises(ValueError):
                    atlas.download(skill, dest)
            self.assertFalse(dest.exists())
            self.assertFalse(list(root.glob(".atlas-*")))

    def test_symlinks_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill, data = self.fixture(root)
            manifest = [{"path": "SKILL.md", "sha": atlas.blob_sha(data), "mode": "120000", "type": "blob"}]
            sha = atlas.manifest_tree_sha(manifest)
            skill["locations"][0]["bundle_sha"] = sha
            (root / "data/manifests.json").write_text(json.dumps({sha: manifest}))
            with patch.object(atlas, "ROOT", root), self.assertRaises(ValueError):
                atlas.bundle_plan(skill["locations"][0])

    def test_dry_run_does_not_fetch_or_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill, _ = self.fixture(root)
            with patch.object(atlas, "ROOT", root), patch.object(atlas, "fetch") as fetch:
                result = atlas.download(skill, root / "result", dry_run=True)
            fetch.assert_not_called()
            self.assertEqual(result["files"], 1)
            self.assertFalse((root / "result").exists())

    def test_runtime_requirement_is_carried_to_download_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill, data = self.fixture(root)
            skill['compatibility'] = 'Requires matching external runtime; copying files is not installation.'
            with patch.object(atlas, 'ROOT', root), patch.object(atlas, 'fetch', return_value=data):
                atlas.download(skill, root / 'result')
            receipt = json.loads((root / 'result/.atlas-receipt.json').read_text())
            self.assertEqual(receipt['compatibility'], skill['compatibility'])


class DeduplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("update", atlas.ROOT / "scripts/update.py")
        cls.update = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.update)

    def variant(self, identifier, bundle, priority=30):
        return {"variant_id": identifier, "name": "demo", "description": "Example", "categories": ["engineering"],
                "location": {"bundle_sha": bundle, "priority": priority}, "instruction_sha256": "same-body", "upstream_category": None,
                "has_external_refs": False, "declared_risk": None, "compatibility": "unknown", "format_issues": []}

    def test_only_identical_complete_bundles_merge(self):
        variants = [self.variant("mirror/demo", "tree-a"), self.variant("publisher/demo", "tree-a", 10), self.variant("other/demo", "tree-b")]
        skills, families, matches = self.update.deduplicate(variants, [])
        self.assertEqual(len(skills), 2)
        merged = next(s for s in skills if s["aliases"])
        self.assertEqual(merged["id"], "publisher/demo")
        self.assertEqual(merged["aliases"], ["mirror/demo"])
        self.assertEqual(len(families), 1)
        self.assertEqual(len(matches), 1)

    def test_yaml_safe_loader_rejects_object_tags(self):
        metadata, _, issue = self.update.frontmatter("---\nname: !!python/object/apply:os.system ['echo unsafe']\n---\nbody")
        self.assertEqual(issue, "invalid_frontmatter")
        self.assertEqual(metadata, {})

    def test_offline_cache_cannot_erase_reviewed_license_for_same_commit(self):
        state = {'commit': 'pinned', 'meta': {'full_name': 'example/repo', 'default_branch': 'HEAD',
                 'archived': None, 'license': None}}
        known = {'repo': 'example/repo', 'commit': 'pinned', 'branch': 'main', 'archived': False,
                 'repository_license': 'MIT'}
        restored = self.update.retain_published_metadata(state, [known])
        self.assertEqual(restored['meta']['license']['spdx_id'], 'MIT')
        self.assertEqual(restored['meta']['default_branch'], 'main')
        self.assertEqual(self.update.retain_published_metadata({**state, 'commit': 'new'}, [known]),
                         {**state, 'commit': 'new'})

    def test_fresh_runner_keeps_license_metadata_when_api_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data").mkdir()
            source = {"repo": "example/repo", "url": "https://github.com/example/repo", "branch": "main",
                      "archived": False, "repository_license": "MIT"}
            (root / "data/catalog.json").write_text(json.dumps({"sources": [source]}))
            with patch.object(self.update, "ROOT", root), patch.object(self.update, "CACHE", root / "cache"), \
                 patch.object(self.update.subprocess, "run"), \
                 patch.object(self.update.subprocess, "check_output", side_effect=[b"", b"111\n", b"222\n", b""]), \
                 patch.dict(self.update.os.environ, {"GITHUB_TOKEN": "test-only-placeholder"}), \
                 patch.object(atlas, "api", side_effect=urllib.error.URLError("unavailable")):
                snapshot = self.update.git_snapshot("example/repo")
            self.assertEqual(snapshot["meta"]["license"]["spdx_id"], "MIT")
            self.assertEqual(snapshot["meta"]["default_branch"], "main")


if __name__ == "__main__":
    unittest.main()
