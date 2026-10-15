#!/usr/bin/env python3
"""Offline consistency checks for the generated catalog and every bundle manifest."""
import json
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import atlas


def main():
    data = atlas.catalog()
    manifests = json.loads((atlas.ROOT / "data/manifests.json").read_text(encoding="utf-8"))
    taxonomy = json.loads((atlas.ROOT / "taxonomy.json").read_text(encoding="utf-8"))["categories"]
    categories = {c["id"] for c in taxonomy}
    identifiers = set()
    bundles = set()
    count = 0
    for skill in data["skills"]:
        for identifier in [skill["id"], *skill["aliases"]]:
            assert identifier not in identifiers, "重复 ID: " + identifier
            identifiers.add(identifier)
        assert skill["categories"] and set(skill["categories"]) <= categories
        assert skill["locations"]
        bundle = skill["locations"][0]["bundle_sha"]
        assert bundle not in bundles, "完整目录未去重"
        bundles.add(bundle)
        for location in skill["locations"]:
            assert re.fullmatch(r"[0-9a-f]{40}", location["commit"])
            assert location["bundle_sha"] == bundle
            atlas.safe_relative(location["path"])
            assert location["url"].startswith("https://github.com/")
            assert location["commit"] in location["url"]
        manifest = manifests[bundle]
        assert atlas.manifest_tree_sha(manifest) == bundle, "清单与完整目录指纹不同: " + skill["id"]
        assert any(f["path"] == "SKILL.md" and f["sha"] == skill["locations"][0]["skill_sha"] for f in manifest)
        count += len(manifest)
    assert data["stats"]["unique_bundles"] == len(data["skills"])
    assert data["stats"]["scanned_skills"] == len(identifiers)
    assert sum(s["skills_scanned"] for s in data["sources"]) == len(identifiers)
    print("验证通过：{} 个技能目录，{} 个来源位置，{} 个文件指纹。".format(len(bundles), len(identifiers), count))


if __name__ == "__main__":
    main()
