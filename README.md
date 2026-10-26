# Skills Atlas

先查少量精选用途，再比较同用途候选。支持中文搜索、来源仓库 Star 提示、独立技能仓库标亮和单项下载。

[工具箱](toolboxes/README.md) · [在线搜索](https://rainlt.github.io/skills-atlas/) · [精选速查](SHORTLIST.md) · [完整目录](CATALOG.md) · [下载工具](https://rainlt.github.io/skills-atlas/skills-atlas-tools.zip)

<!-- STATS:START -->
目前收录 17 个来源、4,148 个技能目录，分为 17 类。默认展示 12 个精选用途，相近候选收拢为 4,017 个入口。
<!-- STATS:END -->

## 工具箱 · 从技能库提炼的工作线

把同类技能整理成一套能衔接执行的工具，按当前材料进入，只调用当前需要的部分。后续新增的领域工具箱统一收在[工具箱板块](toolboxes/README.md)，[在线查看](https://rainlt.github.io/skills-atlas/#toolboxes)。

目前已有 **[科研工具箱](https://github.com/Rainlt/methods-atlas/tree/main/toolboxes/research-toolbox)**：调研 → 定题与研究方案 → 实验 → 分析 → 写作 → 复核交付；引用、绘图与中文清理按需嵌入。例如已有实验结果，可以直接分析、出图并写结果段落。

另有 **[动画制作工具箱](https://github.com/Rainlt/methods-atlas/tree/main/toolboxes/animation-toolbox)**：材料核对 → 讲稿与分镜 → 动画小样 → 导出与检查。整合论文转动画、vibe 方法与 HyperFrames / Remotion；例如把论文方法做成 30 秒模块流程动画。

正文在私有个人方法库中统一维护，需有访问权限；本库保留轻量索引与核对版本，不重复维护上游全文，也不占单项技能精选名额。

```bash
python3 atlas.py toolboxes 科研 --json
```

## 使用

打开[在线搜索](https://rainlt.github.io/skills-atlas/)，默认查看精选；也可切换科研与文档、平台集成、全部目录、观察与归档。查到用途后展开候选比较，各实现的文件、许可和下载 ID 分别保留。

给 AI 查技能时，优先使用下面的简短查询，默认最多返回 5 个用途，精选未命中才扩展全库。不要先读取完整目录和全部上游说明。

```bash
python3 atlas.py search '文献综述' --json
python3 atlas.py search 'pdf' --all --source anthropics
```

需要下载时，先解压[工具包](https://rainlt.github.io/skills-atlas/skills-atlas-tools.zip)，在解压目录运行命令。需要 **Python 3.9+**，无需额外安装 Python 包。

```bash
python3 atlas.py search '科研'
python3 atlas.py search 'debug' --source obra
```

搜索结果会给出完整 ID。以 Superpowers 的调试技能为例：

```bash
python3 atlas.py show obra/superpowers/skills/systematic-debugging
python3 atlas.py download obra/superpowers/skills/systematic-debugging --dest ./downloads/systematic-debugging
```

下载会保留该技能的完整目录，包括脚本、模板和参考资料，并校验文件。已有目录不会被覆盖。下载后的依赖配置和使用方法见技能内的 `SKILL.md`。

打包成 ZIP、指定安装目录等用法见[命令行说明](docs/USAGE.md)。克隆仓库后也可以直接运行这些命令，或打开 `browse.html` 离线搜索。

## 收录与去重

来源包括 [awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)、[agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills)，以及 Anthropic、OpenAI、Vercel、Hugging Face 等项目。完整名单和收录版本见[来源列表](docs/SOURCES.md)。

只有整个技能目录的文件和结构一致时才物理去重；同名或说明相同的不同实现收在一个候选入口下，仍可分别下载。同名不等于功能等价。具体规则见[整理方法](docs/METHODOLOGY.md)。

精选与退出由 [curation.json](curation.json) 管理，默认上限 40 个用途。版本变化、复查到期或候选到期会转观察；人工归档保留原因、日期和替代项。Star 是来源仓库关注度，不是技能评分；缺失或过期时不假定为零，不用 Star 代替核对依据。见[精选与退出规则](docs/CURATION.md)。

## 更新

每周一北京时间 **09:20** 更新已有来源，并独立搜索、核实新来源。有变化就提交 PR，审核合并后更新在线目录和下载工具包。新候选及核实结果见[发现报告](docs/DISCOVERY.md)，不会自动安装或直接进入下载目录。

也可以在 Actions 中手动运行 **Refresh catalog**。本地更新见[维护说明](docs/UPDATES.md)，网页发布见 [GitHub Pages 配置](docs/PAGES.md)。

## 贡献

欢迎提交新来源、纠正分类或补充许可信息。来源配置在 [sources.json](sources.json)，分类和搜索词在 [taxonomy.json](taxonomy.json)。现有格式问题和待核实项见[质量记录](docs/QUALITY.md)。

## 许可

本项目工具代码采用 [MIT](LICENSE)。各技能沿用上游许可证，使用前请查看其授权说明。
