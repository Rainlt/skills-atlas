#!/usr/bin/env python3
"""Package only the public search page and a minimal selective-download toolkit."""
import argparse
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOOL_FILES = ("atlas.py", "catalog_model.py", "taxonomy.json", "data/catalog.json", "data/manifests.json", "data/curated.json", "data/shortlist.json", "LICENSE")


def build(output):
    page = (ROOT / "browse.html").read_text(encoding="utf-8")
    payload = re.search(r'<script id="atlas-data" type="application/json">(.*?)</script>', page, re.S)
    if not payload:
        raise ValueError("搜索页面缺少目录数据")
    embedded = json.loads(payload[1])
    catalog = json.loads((ROOT / "data/catalog.json").read_text(encoding="utf-8"))
    if embedded["snapshot"] != catalog["snapshot"] or len(embedded["skills"]) != len(catalog["skills"]):
        raise ValueError("搜索页面与索引版本不一致，请先运行 scripts/render.py")
    curated = json.loads((ROOT / 'data/curated.json').read_text(encoding='utf-8'))
    short = json.loads((ROOT / 'data/shortlist.json').read_text(encoding='utf-8'))
    if embedded.get('curation_version') != curated['curation_version'] or short['curation_version'] != curated['curation_version']:
        raise ValueError('页面、精选与下载工具包的版本不一致')
    output.mkdir(parents=True, exist_ok=True)
    for filename in ("index.html", "browse.html"):
        (output / filename).write_text(page, encoding="utf-8")
    (output / ".nojekyll").write_text("", encoding="utf-8")
    # Explicit allowlist: source caches, credentials, Git history and upstream skill
    # instructions cannot enter either the site or its downloadable toolkit.
    archive_path = output / "skills-atlas-tools.zip"
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for filename in TOOL_FILES:
            source = ROOT / filename
            if source.is_symlink() or not source.is_file():
                raise ValueError("工具包文件缺失或为链接: " + filename)
            archive.write(source, filename)
        archive.writestr("使用说明.txt", "Skills Atlas 轻量下载工具\n\n需要 Python 3.9 或更新版本。\n在本目录打开终端，运行网页卡片复制的单项下载命令。\n例如：python3 atlas.py search pdf\n下载只获取选中的技能目录及授权告示，不执行技能。\n完整说明：https://github.com/Rainlt/skills-atlas#readme\n")
    print("GitHub Pages 已打包：{} 个技能；工具包 {} 字节。".format(len(catalog["skills"]), archive_path.stat().st_size))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "_site")
    build(parser.parse_args().output)
