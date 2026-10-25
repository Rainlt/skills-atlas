# 科研与资料获取来源补充核对

核对日期：2026-10-25。补齐此前已讨论但未进入索引的三个来源。只索引说明摘要、固定版本和完整文件清单；不公开镜像上游技能正文。

| 来源 | 索引范围 | 核对与使用条件 |
|---|---|---|
| [Adkid-Zephyr/oral-paper-skill](https://github.com/Adkid-Zephyr/oral-paper-skill/tree/a2c4bc41b3aa6946b2ccce1c844ce9936ef83308) | `skills/oral-paper-skill/`，1 个技能、6 个文件 | 完整下载已校验；案例主要为摘要级材料，适用于相关研究的贡献与证据梳理，不能当作录用预测。该固定版本未发现明确许可证，授权保留待核实状态 |
| [larashero3-dotcom/lieflat-less-ai-tone](https://github.com/larashero3-dotcom/lieflat-less-ai-tone/tree/27d29232f10124db904ca9c0536d0b67cb3b2833) | 仓库根目录，1 个技能、12 个文件 | 完整下载已校验，MIT；只按具体规则处理中文成稿，保留结构、事实与作者风格，未在真实论文任务中验证 |
| [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach/tree/14c213405669414492bda0f8d52cc6531d062c45) | `agent_reach/skill/`，1 个技能、5 个文件 | 核对到的 SKILL.md 含版本和渠道占位符，是发布模板；运行需官方程序、生成的技能及相应渠道配置。未安装运行时，未验证平台读取效果 |

根目录技能以仓库名作为 ID，`location.path` 为 `.`，完整清单包括根目录许可和参考文件。下载时使用准确的仓库根路径，文件自身仍通过原有相对路径、类型与 Git 指纹检查；不放宽 `..`、绝对路径和符号链接限制。

Oral Paper 与 Lieflat 各自提供一个新用途入口，进入精选；已有科研用途不增加重复默认项。Agent Reach 属于条件性补充，不因 Star 数直接进入精选。原有 14 个来源仍使用原固定版本；本次只新增 3 个条目，无移除。

验证：新增根目录扫描和实际远端路径回归测试；完整目录验证、38 项测试和生成一致性检查通过。下载验证只说明文件完整性，不表示科研结论、所有运行依赖或第三方平台效果已验证。
