import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def generate(data, taxonomy):
    stats = data["stats"]
    line = "目前收录 {} 个来源、{:,} 个技能目录，分为 {} 类。".format(
        stats["sources"], stats["unique_bundles"], len(taxonomy))
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    text = re.sub(r"<!-- STATS:START -->.*?<!-- STATS:END -->", "<!-- STATS:START -->\n" + line + "\n<!-- STATS:END -->", text, flags=re.S)
    readme.write_text(text, encoding="utf-8")
    quality = {"format_issue_entries": sum(bool(s["format_issues"]) for s in data["skills"]),
               "license_review_entries": sum(s["locations"][0]["license"]["review_required"] for s in data["skills"]),
               "external_reference_entries": sum(s["has_external_refs"] for s in data["skills"]),
               "declared_risk_entries": sum(s["declared_risk"] is not None for s in data["skills"])}
    lines = ["# 质量与待核实记录", "", "这是结构检查与上游声明记录，不是人工评测、安全扫描或许可结论。", "",
             "| 指标 | 条目数 |", "|---|---:|",
             "| 缺少技能级许可声明，需核实具体授权 | {} |".format(quality["license_review_entries"]),
             "| 名称、目录或 frontmatter 等格式问题 | {} |".format(quality["format_issue_entries"]),
             "| 含父目录引用或插件根目录变量等依赖线索 | {} |".format(quality["external_reference_entries"]),
             "| 有上游自报 risk 字段 | {} |".format(quality["declared_risk_entries"]), "",
             "各指标可以重叠。未标注风险不表示安全；有 license 字段也不表示宽松开源。完整字段可用 `atlas.py show <ID>` 查看。", "",
             "格式问题示例（最多 100 项；完整列表在 catalog 的 format_issues）：", "", "| 条目 | 记录 |", "|---|---|"]
    for skill in [s for s in data["skills"] if s["format_issues"]][:100]:
        lines.append("| `{}` | {} |".format(skill["id"].replace("|", "\\|"), ", ".join(skill["format_issues"])))
    (ROOT / "docs/QUALITY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    slim = {"snapshot": data["snapshot"], "generated_at": data["generated_at"], "stats": stats,
            "categories": taxonomy, "sources": [s["repo"] for s in data["sources"]], "skills": []}
    for s in data["skills"]:
        loc = s["locations"][0]
        slim["skills"].append({"id": s["id"], "name": s["name"], "description": s["description"],
                               "categories": s["categories"], "aliases": s["aliases"],
                               "sources": list(dict.fromkeys(x["repo"] for x in s["locations"])),
                               "url": loc["url"], "commit": loc["commit"], "license": loc["license"],
                               "external": s["has_external_refs"], "risk": s["declared_risk"],
                               "compatibility": s["compatibility"], "format_issues": s["format_issues"]})
    payload = json.dumps(slim, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    template = (ROOT / "web/catalog.template.html").read_text(encoding="utf-8")
    (ROOT / "browse.html").write_text(template.replace("__DATA__", payload), encoding="utf-8")


if __name__ == "__main__":
    generate(json.loads((ROOT / "data/catalog.json").read_text(encoding="utf-8")),
             json.loads((ROOT / "taxonomy.json").read_text(encoding="utf-8"))["categories"])
