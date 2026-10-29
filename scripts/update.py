#!/usr/bin/env python3
"""Refresh metadata only. Upstream instructions are parsed as data, never executed."""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import subprocess
import urllib.error
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import atlas
try:
    import yaml
except ImportError:
    raise SystemExit("更新索引需要 PyYAML：python3 -m pip install -r requirements-dev.txt")

ROOT = atlas.ROOT
CACHE = Path(os.environ.get("ATLAS_CACHE_DIR", str(ROOT / ".cache")))
OFFLINE = False


def git_snapshot(repo, existing_meta=None, pinned_commit=None):
    """Fetch commit/tree objects only; skill files are fetched individually below."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError("来源仓库名不合法")
    if pinned_commit is not None and not re.fullmatch(r'[0-9a-f]{40}', pinned_commit):
        raise ValueError('pinned_commit must be a full lowercase commit SHA')
    folder = CACHE / "git" / (repo.replace("/", "--") + ".git")
    folder.parent.mkdir(parents=True, exist_ok=True)
    def git(*args):
        return subprocess.check_output(["git", "-c", "core.hooksPath=/dev/null", "-C", str(folder), *args],
                                       stderr=subprocess.PIPE, timeout=180).decode()
    if not folder.exists():
        subprocess.run(["git", "init", "--bare", str(folder)], check=True, capture_output=True)
    git("fetch", "--depth=1", "--filter=blob:none", "--no-tags", "https://github.com/" + repo + ".git", pinned_commit or "HEAD")
    commit = git("rev-parse", "FETCH_HEAD").strip()
    if pinned_commit and commit != pinned_commit:
        raise ValueError('Fetched commit differs from source pin')
    tree_sha = git("rev-parse", "FETCH_HEAD^{tree}").strip()
    rows = git("ls-tree", "-r", "-t", "--full-tree", "-z", "FETCH_HEAD").split("\0")
    items = []
    for row in rows:
        if not row:
            continue
        info, path = row.split("\t", 1)
        mode, kind, sha = info.split()
        items.append({"mode": mode, "type": kind, "sha": sha, "path": path})
    # Hosted runners start without the local source cache. Retain committed metadata
    # if the API is unavailable, instead of replacing known license hints with UNKNOWN.
    if not existing_meta and (ROOT / "data/catalog.json").exists():
        previous = json.loads((ROOT / "data/catalog.json").read_text(encoding="utf-8"))
        source = next((s for s in previous["sources"] if s["repo"] == repo), None)
        if source:
            existing_meta = {"full_name": repo, "html_url": source["url"], "default_branch": source["branch"],
                             "archived": source["archived"], "license": {"spdx_id": source["repository_license"]}}
    meta = existing_meta or {"full_name": repo, "html_url": "https://github.com/" + repo,
                             "default_branch": "HEAD", "archived": None, "license": None}
    if os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"):
        try:
            meta = atlas.api("repos/" + repo)
        except (urllib.error.URLError, ValueError) as exc:
            print("仓库元数据接口暂不可用，保留已知信息：{} ({})".format(repo, type(exc).__name__), flush=True)
    return {"meta": meta, "tree": {"sha": tree_sha, "tree": items, "truncated": False}, "commit": commit}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cached_blob(repo, commit, path, sha):
    cache = CACHE / "blobs" / sha
    if cache.exists():
        data = cache.read_bytes()
        if atlas.blob_sha(data) == sha:
            return data
    if OFFLINE:
        raise ValueError("离线缓存缺失或校验失败: " + path)
    data = atlas.fetch(atlas.raw_url(repo, commit, path))
    if atlas.blob_sha(data) != sha:
        raise ValueError("上游文件校验失败: " + path)
    cache.parent.mkdir(parents=True, exist_ok=True)
    temp = cache.with_suffix("." + hashlib.sha256(path.encode()).hexdigest()[:12] + ".tmp")
    temp.write_bytes(data)
    temp.replace(cache)
    return data


def frontmatter(text):
    match = re.match(r"\A\ufeff?---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|$)", text, re.S)
    if not match:
        return {}, text, "missing_frontmatter"
    try:
        meta = yaml.safe_load(match[1])
        if not isinstance(meta, dict):
            raise ValueError("frontmatter must be a mapping")
        return meta, text[match.end():], None
    except (yaml.YAMLError, ValueError):
        return {}, text, "invalid_frontmatter"


def classify(name, description, source, taxonomy, upstream_category=None, category_map=None):
    weighted = []
    name = name.lower().replace("_", "-")
    description = description.lower()
    for category in taxonomy:
        score = sum(6 * bool(re.search(r"(?<![a-z0-9])" + re.escape(k) + r"(?:s|es|ing|ed)?(?![a-z0-9])", name)) +
                    2 * bool(re.search(r"(?<![a-z0-9])" + re.escape(k) + r"(?:s|es|ing|ed)?(?![a-z0-9])", description))
                    for k in category["keywords"])
        if category["id"] == (category_map or {}).get(upstream_category):
            score += 10
        if category["id"] == "research" and "scientific-agent" in source:
            score += 15
        if category["id"] == "security" and source.startswith("trailofbits/"):
            score += 15
        if category["id"] == "ai" and source.startswith(("huggingface/", "google-gemini/")):
            score += 10
        if score:
            weighted.append((-score, category["id"]))
    ordered = sorted(weighted)
    return [v for _, v in ordered[:3]] or ["other"]


def notice_file(path):
    name = PurePosixPath(path).name.upper()
    return bool(re.match(r"^(?:UPSTREAM-)?(?:LICENSE|LICENCE|COPYING|NOTICE|THIRD.PARTY.NOTICES)(?:$|[._-])", name))


def ancestor_notices(path, items):
    parents = {str(p) for p in PurePosixPath(path).parents}
    return [dict(path=x["path"], sha=x["sha"], mode=x["mode"]) for x in items
            if x["type"] == "blob" and str(PurePosixPath(x["path"]).parent) in parents
            and notice_file(x["path"])]


def retain_published_metadata(state, previous_sources):
    """An old offline cache must not erase later-reviewed metadata for the same commit."""
    previous = next((s for s in previous_sources if s['repo'] == state['meta']['full_name']
                     and s['commit'] == state['commit']), None)
    meta = dict(state['meta'])
    if previous:
        if not (meta.get('license') or {}).get('spdx_id') or (meta.get('license') or {}).get('spdx_id') == 'UNKNOWN':
            meta['license'] = {'spdx_id': previous['repository_license']}
        if meta.get('default_branch') in (None, 'HEAD'):
            meta['default_branch'] = previous['branch']
        if meta.get('archived') is None:
            meta['archived'] = previous['archived']
    return {**state, 'meta': meta}


def scan_source(source, taxonomy, offline=False, seed_dir=None):
    repo = source["repo"]
    pin = source.get('pinned_commit')
    if pin is not None and not re.fullmatch(r'[0-9a-f]{40}', pin):
        raise ValueError('pinned_commit must be a full lowercase commit SHA')
    key = repo.replace("/", "--")
    state_path = CACHE / "sources" / (key + ".json")
    if offline:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if pin and state['commit'] != pin:
            raise ValueError('Offline source cache differs from pinned commit: ' + repo)
        published = ROOT / 'data/catalog.json'
        if published.exists():
            state = retain_published_metadata(state, json.loads(published.read_text(encoding='utf-8'))['sources'])
    else:
        seed = seed_dir / (key + ".json") if seed_dir else state_path
        previous_meta = json.loads(seed.read_text(encoding="utf-8"))["meta"] if seed.exists() else None
        state = git_snapshot(repo, previous_meta, pinned_commit=pin) if pin else git_snapshot(repo, previous_meta)
        write_json(state_path, state)
    meta, tree = state["meta"], state["tree"]
    if tree.get("truncated"):
        raise ValueError("拒绝不完整的上游目录树: " + repo)
    commit = state["commit"]
    items = tree["tree"]
    by_path = {x["path"]: x for x in items}
    # A repository can itself be the skill directory (for example Lieflat).
    # Represent that boundary explicitly; file paths remain strictly relative.
    by_path["."] = {"sha": tree["sha"], "type": "tree", "path": "."}
    notice_items = [x for x in items if x["type"] == "blob" and notice_file(x["path"])]
    paths = [x for x in items if x["type"] == "blob" and PurePosixPath(x["path"]).name == "SKILL.md"
             and any(x["path"].startswith(p) for p in source["include"])
             and not any(x["path"].startswith(p) for p in source.get("exclude", []))]
    if not paths:
        raise ValueError("来源白名单内没有 SKILL.md，可能发生目录迁移: " + repo)
    directories = {str(PurePosixPath(x["path"]).parent) for x in paths}
    manifests = {d: [] for d in directories}
    for item in items:
        if item["type"] == "tree":
            continue
        for parent in PurePosixPath(item["path"]).parents:
            directory = str(parent)
            if directory in manifests:
                relative = item["path"] if directory == "." else item["path"][len(directory)+1:]
                manifests[directory].append({"path": relative, "sha": item["sha"], "mode": item["mode"], "type": item["type"]})
    included_by_sha = {by_path[d]["sha"]: d for d in sorted(directories)}
    distribution_groups = collections.defaultdict(list)
    excluded = [x for x in items if x["path"].endswith("/SKILL.md") and str(PurePosixPath(x["path"]).parent) not in directories]
    for item in excluded:
        directory = str(PurePosixPath(item["path"]).parent)
        sha = by_path[directory]["sha"]
        if sha in included_by_sha:
            distribution_groups[sha].append(directory)
    distribution = [{"repo": repo, "bundle_sha": sha, "canonical_path": included_by_sha[sha], "excluded_paths": sorted(group)}
                    for sha, group in sorted(distribution_groups.items())]
    taxonomy_config = json.loads((ROOT / "taxonomy.json").read_text(encoding="utf-8"))
    category_map = taxonomy_config.get("upstream_category_map", {})
    upstream_index = {}
    if repo == "sickn33/agentic-awesome-skills" and "skills_index.json" in by_path:
        index_item = by_path["skills_index.json"]
        index = json.loads(cached_blob(repo, commit, "skills_index.json", index_item["sha"]))
        upstream_index = {x["path"]: x.get("category") for x in index}
    result = []
    issues = []

    def parse(item):
        path = item["path"]
        text = cached_blob(repo, commit, path, item["sha"]).decode("utf-8", errors="replace")
        meta_skill, body, issue = frontmatter(text)
        directory = str(PurePosixPath(path).parent)
        fallback_name = repo.rsplit("/", 1)[-1] if directory == "." else PurePosixPath(directory).name
        name = str(meta_skill.get("name") or fallback_name).strip()
        description = str(meta_skill.get("description") or "").strip()
        problems = [issue] if issue else []
        if not description:
            problems.append("missing_description")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
            problems.append("nonstandard_name")
        if name != fallback_name:
            problems.append("name_directory_mismatch")
        bundle_sha = by_path[directory]["sha"]
        local_license = str(meta_skill.get("license") or "").strip()
        notices = [] if directory == "." else ancestor_notices(directory, notice_items)
        # Preserve declarations as evidence, without treating a repository code license as
        # the license of copied third-party content or of individual skill instructions.
        repository_license = (meta.get("license") or {}).get("spdx_id") or "UNKNOWN"
        inherited = "CC-BY-4.0; third-party exceptions apply" if repo == "sickn33/agentic-awesome-skills" else repository_license
        license_info = {"declared": local_license or None, "repository": repository_license,
                        "content_hint": inherited, "review_required": not bool(local_license),
                        "url": "https://github.com/{}/tree/{}/{}".format(repo, commit, directory)}
        normalized = re.sub(r"\s+", " ", body).strip()
        upstream_category = upstream_index.get(directory)
        categories = classify(name, description, repo, taxonomy, upstream_category, category_map)
        categories = taxonomy_config.get("name_overrides", {}).get(name, categories)
        metadata = meta_skill.get("metadata") if isinstance(meta_skill.get("metadata"), dict) else {}
        risk = meta_skill.get("risk") or metadata.get("risk")
        # Small descriptions are indexed, full instructions are neither mirrored nor published.
        return {"variant_id": repo if directory == "." else repo + "/" + directory, "name": name, "manifest": manifests[directory], "upstream_category": upstream_category,
                "description": description, "categories": categories,
                "instruction_sha256": hashlib.sha256(normalized.encode()).hexdigest(),
                "has_external_refs": bool(re.search(r"(?:\.\./|\$\{?(?:CLAUDE_PLUGIN_ROOT|CODEX_HOME)|\$\{?SKILL_ROOT)", body)),
                "declared_risk": str(risk) if risk is not None else None,
                "compatibility": "；".join(str(v) for v in [source.get("compatibility"), meta_skill.get("compatibility")]
                                             if v) or "未验证；请阅读上游要求",
                "format_issues": problems,
                "location": {"repo": repo, "path": directory, "commit": commit,
                             "bundle_sha": bundle_sha, "skill_sha": item["sha"],
                             "url": "https://github.com/{}/tree/{}/{}".format(repo, commit, directory),
                             "priority": source["priority"], "kind": source["kind"],
                             "license": license_info, "notices": notices}}

    print("扫描 {}：{} 个主目录技能".format(repo, len(paths)), flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(parse, p): p for p in paths}
        done = 0
        for future in concurrent.futures.as_completed(futures):
            try:
                result.append(future.result())
            except Exception as exc:
                issues.append({"path": futures[future]["path"], "error": str(exc)})
            done += 1
            if done % 500 == 0:
                print("  {}/{}".format(done, len(paths)), flush=True)
    if issues:
        raise ValueError("来源抓取不完整，保留旧索引：" + json.dumps(issues[:10], ensure_ascii=False))
    source_state = {**source, "repo": meta["full_name"], "commit": commit, "tree_sha": tree["sha"],
                    "branch": meta["default_branch"], "archived": meta["archived"],
                    "repository_license": (meta.get("license") or {}).get("spdx_id") or "UNKNOWN",
                    "skills_scanned": len(paths), "url": meta["html_url"]}
    source_state["excluded_skill_files"] = len(excluded)
    source_state["excluded_identical_distribution_copies"] = sum(len(x["excluded_paths"]) for x in distribution)
    # README references are a discovery queue, not presumed installable or trusted skills.
    references = []
    if source["kind"] == "collection" and source.get('discover_references', True):
        readme = by_path.get("README.md")
        if readme:
            text = cached_blob(repo, commit, "README.md", readme["sha"]).decode("utf-8", "replace")
            urls = sorted(set(re.findall(r"https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)(?=[/#?)\s]|$)", text)))
            references = [{"repo": x.rstrip("."), "discovered_in": repo, "status": "unverified_reference"} for x in urls if x.lower() != repo.lower()]
    return result, source_state, references, distribution


def deduplicate(variants, taxonomy):
    groups = collections.defaultdict(list)
    for v in variants:
        groups[v["location"]["bundle_sha"]].append(v)
    skills = []
    for group in groups.values():
        group.sort(key=lambda v: (v["location"]["priority"], v["variant_id"]))
        head = group[0]
        categories = head["categories"]
        skills.append({"id": head["variant_id"], "name": head["name"], "description": head["description"],
                       "categories": categories, "tags_zh": [c["name_zh"] for c in taxonomy if c["id"] in categories],
                       "aliases": [v["variant_id"] for v in group[1:]],
                       "locations": [v["location"] for v in group],
                       "instruction_sha256": head["instruction_sha256"],
                       "upstream_category": head["upstream_category"],
                       "declared_risk": head["declared_risk"], "compatibility": head["compatibility"],
                       "has_external_refs": any(v["has_external_refs"] for v in group),
                       "format_issues": sorted({p for v in group for p in v["format_issues"]})})
    skills.sort(key=lambda s: s["id"])
    names = collections.defaultdict(list)
    instruction_groups = collections.defaultdict(list)
    for skill in skills:
        names[skill["name"].lower()].append(skill["id"])
        instruction_groups[skill["instruction_sha256"]].append(skill["id"])
    families = [{"name": n, "members": ids, "status": "same_name_kept_separate"} for n, ids in sorted(names.items()) if len(ids) > 1]
    instruction_matches = [{"instruction_sha256": h, "members": ids, "status": "same_instructions_different_bundle"}
                           for h, ids in sorted(instruction_groups.items()) if len(ids) > 1]
    return skills, families, instruction_matches


def markdown_cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ").replace("\r", " ").replace("<", "&lt;").replace(">", "&gt;").replace("[", "\\[").replace("]", "\\]")


def render_catalog(data, taxonomy):
    docs = ROOT / "docs/categories"
    docs.mkdir(parents=True, exist_ok=True)
    lines = ["# 技能分类目录", "", "索引快照：`{}`。主分类用于下表计数；交叉标签可在命令行筛选。".format(data["snapshot"]), "",
             "搜索：`python3 atlas.py search '科研'`。查看条目：`python3 atlas.py show <ID>`。", "",
             "| 分类 | 去重后条目 |", "|---|---:|"]
    for category in taxonomy:
        skills = [s for s in data["skills"] if s["categories"][0] == category["id"]]
        lines.append("| [{}](docs/categories/{}.md) | {} |".format(category["name_zh"], category["id"], len(skills)))
        content = ["# " + category["name_zh"], "", "[返回总目录](../../CATALOG.md) · {} 个条目 · 分类为规则初分，欢迎纠错。".format(len(skills)), "",
                   "复制完整 ID 后运行 `python3 atlas.py download <ID> --dest ./downloads/<目录名>`。", "",
                   "| 名称与来源 | 用途（上游原文） | 完整 ID |", "|---|---|---|"]
        for skill in skills:
            content.append("| [{}]({}) | {} | `{}` |".format(markdown_cell(skill["name"]), skill["locations"][0]["url"],
                           markdown_cell(skill["description"][:220]), markdown_cell(skill["id"])))
        (docs / (category["id"] + ".md")).write_text("\n".join(content) + "\n", encoding="utf-8")
    (ROOT / "CATALOG.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    source_lines = ["# 来源与快照", "", "只扫描明确列入 `sources.json` 的目录；外部链接另外进入待核实队列。", "",
                    "| 来源 | 类型 | 技能数 | 固定版本 | 仓库级许可证线索 |", "|---|---|---:|---|---|"]
    for source in data["sources"]:
        source_lines.append("| [{}]({}) | {} | {} | [{}]({}/commit/{}) | {} |".format(source["repo"], source["url"], source["kind"],
                            source["skills_scanned"], source["commit"][:12], source["url"], source["commit"], source["repository_license"]))
    source_lines += ["", "仓库级许可证只是线索，不覆盖技能中的单独授权；UNKNOWN 表示未被 GitHub 识别。", "",
                     "详细授权声明与保留的上游 notice 见各条目的 `locations[].license` 和 `notices`。", ""]
    (ROOT / "docs/SOURCES.md").write_text("\n".join(source_lines), encoding="utf-8")


def main():
    global OFFLINE
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="从已缓存的固定版本重新生成索引")
    parser.add_argument("--seed-dir", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    OFFLINE = args.offline
    sources = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))["sources"]
    taxonomy = json.loads((ROOT / "taxonomy.json").read_text(encoding="utf-8"))["categories"]
    variants, states, references, distribution_copies = [], [], [], []
    # Fail closed: any failed source leaves the committed catalog untouched.
    for source in sources:
        v, state, refs, copies = scan_source(source, taxonomy, args.offline, args.seed_dir)
        variants.extend(v)
        states.append(state)
        references.extend(refs)
        distribution_copies.extend(copies)
    skills, families, matches = deduplicate(variants, taxonomy)
    snapshot_inputs = {"revisions": [(s["repo"], s["commit"]) for s in states], "sources": sources,
                       "taxonomy": json.loads((ROOT / "taxonomy.json").read_text(encoding="utf-8")), "format_version": 1}
    snapshot = hashlib.sha256(json.dumps(snapshot_inputs, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
    old_path = ROOT / "data/catalog.json"
    old = json.loads(old_path.read_text(encoding="utf-8")) if old_path.exists() else {"skills": []}
    old_by_id = {s["id"]: s for s in old["skills"]}
    new_by_id = {s["id"]: s for s in skills}
    delta = {"added": sorted(new_by_id.keys() - old_by_id.keys()), "removed": sorted(old_by_id.keys() - new_by_id.keys()),
             "updated": sorted(k for k in old_by_id.keys() & new_by_id.keys()
                               if old_by_id[k]["locations"][0]["bundle_sha"] != new_by_id[k]["locations"][0]["bundle_sha"]),
             "reclassified": sorted(k for k in old_by_id.keys() & new_by_id.keys() if old_by_id[k]["categories"] != new_by_id[k]["categories"])}
    data = {"schema_version": 1, "snapshot": snapshot,
            "generated_at": old.get("generated_at") if old.get("snapshot") == snapshot else datetime.now(timezone.utc).isoformat(),
            "stats": {"sources": len(states), "scanned_skills": len(variants), "unique_bundles": len(skills),
                      "exact_duplicates_removed": len(variants) - len(skills), "same_name_families": len(families),
                      "excluded_identical_distribution_copies": sum(s["excluded_identical_distribution_copies"] for s in states),
                      "excluded_noncanonical_skill_files": sum(s["excluded_skill_files"] for s in states),
                      "identical_instruction_groups": len(matches)}, "sources": states, "skills": skills}
    write_json(ROOT / "data/catalog.json", data)
    write_json(ROOT / "data/manifests.json", {v["location"]["bundle_sha"]: v["manifest"] for v in sorted(variants, key=lambda v: v["variant_id"])})
    write_json(ROOT / "data/duplicates.json", {"exact_groups": [{"id": s["id"], "aliases": s["aliases"]} for s in skills if s["aliases"]],
                                              "same_name_families": families, "instruction_matches": matches,
                                              "excluded_distribution_copies": distribution_copies})
    from scripts.discover import merge_queue
    queue_path = ROOT / "data/discovery-queue.json"
    previous_queue = json.loads(queue_path.read_text(encoding="utf-8")) if queue_path.exists() else []
    discovery = json.loads((ROOT / 'discovery.json').read_text(encoding='utf-8'))
    write_json(queue_path, merge_queue(previous_queue, references, [s["repo"] for s in sources],
                                       discovery.get('excluded_repositories', [])))
    # A no-op run should not replace the last meaningful change report.
    if old.get("snapshot") != snapshot:
        write_json(ROOT / "data/changes.json", {"previous_snapshot": old.get("snapshot"), "snapshot": snapshot, **delta})
    render_catalog(data, taxonomy)
    from scripts.curate import generate as generate_curation
    generate_curation(data, as_of=datetime.now(timezone(timedelta(hours=8))).date().isoformat())
    from scripts.render import generate
    generate(data, taxonomy)
    print(json.dumps(data["stats"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
