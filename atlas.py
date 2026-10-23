#!/usr/bin/env python3
"""Search and download one pinned skill. Python 3.9+, standard library only."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent
MAX_FILE = 32 * 1024 * 1024
MAX_BUNDLE = 128 * 1024 * 1024


def fetch(url, *, limit=MAX_FILE, attempts=4):
    headers = {"User-Agent": "skills-atlas/1.0", "Accept": "application/vnd.github+json"}
    # Credentials are sent only to the GitHub API, never to raw content hosts.
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token and urllib.parse.urlparse(url).netloc == "api.github.com":
        headers["Authorization"] = "Bearer " + token
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=45) as response:
                data = response.read(limit + 1)
            if len(data) > limit:
                raise ValueError("文件超过大小限制: " + url)
            return data
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == attempts - 1:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == attempts - 1:
                raise
        time.sleep(2 ** attempt)


def api(path):
    return json.loads(fetch("https://api.github.com/" + path, limit=48 * 1024 * 1024))


def raw_url(repo, commit, path):
    return "https://raw.githubusercontent.com/{}/{}/{}".format(repo, commit, urllib.parse.quote(path, safe="/"))


def blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def safe_relative(path):
    p = PurePosixPath(path)
    if not path or p.is_absolute() or any(x in ("", ".", "..") for x in path.split("/")) or "\\" in path or "\0" in path or ":" in path:
        raise ValueError("不安全的上游文件路径: " + repr(path))
    # Refuse hidden VCS/config paths and Windows special filenames at every level.
    if any(part.lower() == ".git" or re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part) for part in p.parts):
        raise ValueError("不安全的上游文件名: " + repr(path))
    return p


def manifest_tree_sha(items):
    root = {}
    for item in items:
        parts = safe_relative(item["path"]).parts
        node = root
        for part in parts[:-1]:
            child = node.setdefault(part, {})
            if not isinstance(child, dict):
                raise ValueError("文件清单存在目录冲突")
            node = child
        if parts[-1] in node:
            raise ValueError("文件清单路径重复")
        node[parts[-1]] = (item["mode"], item["sha"])
    def digest(node):
        body = b""
        for name, value in sorted(node.items(), key=lambda x: (x[0] + ("/" if isinstance(x[1], dict) else "")).encode()):
            mode, sha = ("40000", digest(value)) if isinstance(value, dict) else value
            body += mode.encode() + b" " + name.encode() + b"\0" + bytes.fromhex(sha)
        return hashlib.sha1(b"tree " + str(len(body)).encode() + b"\0" + body).hexdigest()
    return digest(root)


def catalog():
    return json.loads((ROOT / "data/catalog.json").read_text(encoding="utf-8"))


def resolve_skill(data, identifier):
    found = [s for s in data["skills"] if identifier == s["id"] or identifier in s["aliases"]]
    if not found:
        found = [s for s in data["skills"] if identifier == s["name"]]
    if len(found) != 1:
        choices = ", ".join(s["id"] for s in found[:15])
        raise ValueError("技能 ID 不存在或名称有多个实现，请使用完整 ID。" + (" 候选: " + choices if choices else ""))
    return found[0]


def search(data, query="", category=None, source=None, limit=30):
    taxonomy = json.loads((ROOT / "taxonomy.json").read_text(encoding="utf-8"))["categories"]
    terms = query.lower().split()
    # Chinese phrases expand to an OR group of domain keywords; query groups combine with AND.
    groups = []
    for term in terms:
        matching = [c for c in taxonomy if term in c["queries_zh"] or term == c["name_zh"]]
        groups.append([term] + [v for c in matching for v in c["keywords"]] + [c["id"] for c in matching])
    ranked = []
    for skill in data["skills"]:
        if category and category not in skill["categories"]:
            continue
        if source and not any(source.lower() in x["repo"].lower() for x in skill["locations"]):
            continue
        hay = " ".join([skill["id"], skill["name"], skill["description"], *skill["categories"], *skill.get("tags_zh", [])]).lower()
        if all(any(t in hay for t in group) for group in groups):
            score = sum(10 if term in skill["name"].lower() else 1 for term in terms)
            ranked.append((-score, skill["id"], skill))
    return [x[2] for x in sorted(ranked)[:limit]]


def bundle_plan(location):
    manifests = json.loads((ROOT / "data/manifests.json").read_text(encoding="utf-8"))
    items = manifests.get(location["bundle_sha"])
    if not items:
        raise ValueError("索引缺少此技能的文件清单")
    if manifest_tree_sha(items) != location["bundle_sha"]:
        raise ValueError("文件清单的 Git 目录指纹不匹配")
    files = []
    for item in items:
        safe_relative(item["path"])
        if item["type"] == "tree":
            continue
        if item["type"] != "blob" or item.get("mode") not in ("100644", "100755"):
            raise ValueError("此技能含符号链接、子模块或特殊文件，请直接检查上游: " + item["path"])
        if item.get("size", 0) > MAX_FILE:
            raise ValueError("技能包含超大文件")
        files.append(item)
    if sum(x.get("size", 0) for x in files) > MAX_BUNDLE or len(files) > 3000:
        raise ValueError("技能目录超过下载上限")
    if not any(f["path"] == "SKILL.md" and f["sha"] == location["skill_sha"] for f in files):
        raise ValueError("SKILL.md 与索引不一致")
    return files


def download(skill, dest, *, variant=0, dry_run=False, as_zip=False):
    location = skill["locations"][variant]
    plan = bundle_plan(location)
    summary = {"id": skill["id"], "source": location["url"], "commit": location["commit"],
               "files": len(plan),
               "compatibility": skill.get("compatibility", "未验证；请阅读上游要求"),
               "license": location["license"], "external_references": skill["has_external_refs"]}
    if dry_run:
        return summary
    dest = Path(dest).expanduser()
    if dest.exists():
        raise ValueError("目标已存在，拒绝覆盖: " + str(dest))
    dest.parent.mkdir(parents=True, exist_ok=True)
    if any(x["path"].split("/")[0] in (".atlas-upstream", ".atlas-receipt.json") for x in plan):
        raise ValueError("上游使用了下载器保留的路径")
    with tempfile.TemporaryDirectory(prefix=".atlas-", dir=str(dest.parent)) as temp:
        stage = Path(temp) / "skill"
        stage.mkdir()
        entries = [(f, location["path"] + "/" + f["path"], f["path"]) for f in plan]
        downloaded = [0]
        lock = threading.Lock()
        # Carry ancestor copyright/license notices without modifying upstream skill files.
        for notice in location.get("notices", []):
            out = ".atlas-upstream/" + hashlib.sha256(notice["path"].encode()).hexdigest()[:8] + "-" + PurePosixPath(notice["path"]).name
            entries.append((notice, notice["path"], out))

        def save(entry):
            info, remote_path, out = entry
            target = stage.joinpath(*safe_relative(out).parts)
            data = fetch(raw_url(location["repo"], location["commit"], remote_path))
            if blob_sha(data) != info["sha"]:
                raise ValueError("文件完整性校验失败: " + remote_path)
            with lock:
                downloaded[0] += len(data)
                if downloaded[0] > MAX_BUNDLE:
                    raise ValueError("技能下载超过总大小限制")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            target.chmod(0o755 if info.get("mode") == "100755" else 0o644)

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(save, entries))
        summary["upstream_notices"] = location.get("notices", [])
        summary["bytes"] = downloaded[0]
        (stage / ".atlas-receipt.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if as_zip:
            archive_path = Path(temp) / "bundle.zip"
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
                for p in sorted(stage.rglob("*")):
                    if p.is_file():
                        archive.write(p, skill["name"] + "/" + p.relative_to(stage).as_posix())
            # Publish only a fully verified download. Never overwrite an existing destination.
            with dest.open("xb") as output, archive_path.open("rb") as source:
                shutil.copyfileobj(source, output)
        else:
            # mkdir is exclusive, including for concurrent installs.
            dest.mkdir()
            try:
                for p in stage.iterdir():
                    shutil.move(str(p), str(dest / p.name))
            except BaseException:
                shutil.rmtree(dest)
                raise
    return summary


def main():
    parser = argparse.ArgumentParser(description="Skills Atlas：搜索索引、查看来源、仅下载选中的技能")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("search")
    p.add_argument("query", nargs="?", default="")
    p.add_argument("--category")
    p.add_argument("--source")
    p.add_argument("--limit", type=int, default=30)
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("show")
    p.add_argument("id")
    for cmd in ("download", "install"):
        p = sub.add_parser(cmd, help="只写入指定目录，不运行技能或安装外部依赖")
        p.add_argument("id")
        p.add_argument("--dest" if cmd == "download" else "--target", required=True)
        p.add_argument("--variant", type=int, default=0, help="完全相同文件的来源位置，默认首选来源 0")
        p.add_argument("--dry-run", action="store_true")
        if cmd == "download":
            p.add_argument("--zip", action="store_true")
    args = parser.parse_args()
    try:
        data = catalog()
        if args.command == "search":
            results = search(data, args.query, args.category, args.source, max(1, args.limit))
            if args.json:
                print(json.dumps(results, ensure_ascii=False, indent=2))
            else:
                for s in results:
                    print("{}  [{}]\n  {}\n  {}".format(s["id"], ", ".join(s["categories"]), s["name"], s["description"][:180]))
                print("\n{} 个结果（最多 {} 个）。show <ID> 查看完整信息。".format(len(results), args.limit))
        else:
            skill = resolve_skill(data, args.id)
            if args.command == "show":
                print(json.dumps(skill, ensure_ascii=False, indent=2))
            else:
                if not 0 <= args.variant < len(skill["locations"]):
                    raise ValueError("来源位置编号不存在")
                result = download(skill, args.dest if args.command == "download" else args.target,
                                  variant=args.variant, dry_run=args.dry_run, as_zip=getattr(args, "zip", False))
                print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, urllib.error.URLError) as exc:
        print("错误: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
