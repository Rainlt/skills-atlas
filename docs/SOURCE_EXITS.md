# 已移除来源

本页只保留退出理由与替代入口。条目已从当前技能目录和下载清单移除，不是普通备选；仅当用户明确改变决定时再评估恢复。历史版本仍可从 Git 历史查阅。

| 日期 | 来源及原 ID | 原因 | 替代 |
|---|---|---|---|
| 2026-10-29 | yrui-cmd/cell_su7；`yrui-cmd/cell_su7/plugins/cell_su7/skills/cell_su7` | 用户明确要求删除，表示不会使用小描服务；不代表上游失效 | [image-to-editable-svg](../skills/image-to-editable-svg/SKILL.md)，助手核对文字＋本地描摹，交付 SVG |

原核对版本：`95dce2b972d8b93f36a95e7f045f4d3910a44313`，目录指纹 `2df39275c69b7b65d19ecd9f5210b60fd3a77f42`；[历史核对记录](SOURCE_REVIEW_CELL_SU7.md)。未安装或调用其付费服务。

`discovery.json` 的 excluded_repositories 防止已明确移除的来源再次进入发现候选队列；sources.json 的白名单控制当前实际索引。恢复时须同时更新排除项、白名单和核对记录，不能只改其中一处。
