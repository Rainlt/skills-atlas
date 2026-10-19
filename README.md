# Skills Atlas

汇总多个 GitHub 仓库里的 Agent Skills，按用途分类，支持中文搜索和单项下载。

[在线搜索](https://rainlt.github.io/skills-atlas/) · [分类目录](CATALOG.md) · [下载工具](https://rainlt.github.io/skills-atlas/skills-atlas-tools.zip)

<!-- STATS:START -->
目前收录 12 个来源、3,968 个技能目录，分为 17 类。
<!-- STATS:END -->

## 使用

打开[在线搜索](https://rainlt.github.io/skills-atlas/)，找到技能后可以查看上游说明、复制下载命令。

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

只有整个技能目录的文件和结构一致时才合并；同名或功能相近的不同实现会保留。中文分类和搜索词由本项目整理，技能名称与描述保留原文。具体规则见[整理方法](docs/METHODOLOGY.md)。

## 更新

每周一北京时间 **09:20** 检查上游，有变化就提交 PR。审核合并后，在线目录和下载工具包自动更新。

也可以在 Actions 中手动运行 **Refresh catalog**。本地更新见[维护说明](docs/UPDATES.md)，网页发布见 [GitHub Pages 配置](docs/PAGES.md)。

## 贡献

欢迎提交新来源、纠正分类或补充许可信息。来源配置在 [sources.json](sources.json)，分类和搜索词在 [taxonomy.json](taxonomy.json)。现有格式问题和待核实项见[质量记录](docs/QUALITY.md)。

## 许可

本项目工具代码采用 [MIT](LICENSE)。各技能沿用上游许可证，使用前请查看其授权说明。
