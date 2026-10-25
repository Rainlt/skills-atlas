# 命令行用法

需要 Python 3.9+。解压[工具包](https://rainlt.github.io/skills-atlas/skills-atlas-tools.zip)后，在解压目录运行命令；也可以克隆仓库：

```bash
git clone https://github.com/Rainlt/skills-atlas.git
cd skills-atlas
```

## 搜索

```bash
python3 atlas.py search '科研'
python3 atlas.py search 'pdf' --source anthropics
python3 atlas.py search 'debug' --category testing
python3 atlas.py search '视频' --limit 10
python3 atlas.py search 'postgres' --json
```

默认先读精选，最多输出 5 个用途，未命中时自动扩展全库。同组只显示最匹配的一个入口。`--json` 返回简短对象，含实际搜索范围、是否扩展、用途数量和结果；结果显示核对状态、来源仓库 Star 和候选数。

```bash
python3 atlas.py search 'pdf' --all
python3 atlas.py search '安全' --scope featured --json
python3 atlas.py search '文档' --scope archived --json
python3 atlas.py search 'pdf' --include-archived
python3 atlas.py search 'pdf' --raw --json --limit 30
```

`--raw` 保留原始逐项搜索和完整 JSON 列表的旧格式。`--scope` 还可选 research、integrations、all；`--all` 等价于 `--scope all`。中文词按主题扩展，分类和关键词见 [taxonomy.json](../taxonomy.json)。来源筛选保留子串匹配，例如 `--source anthropics`。

## 查看与下载

`show` 显示来源、固定版本、许可声明和环境要求。`--dry-run` 预览文件数量等信息，不下载文件。

```bash
python3 atlas.py show obra/superpowers/skills/systematic-debugging
python3 atlas.py show openai/skills/skills/.curated/pdf --alternatives
python3 atlas.py download obra/superpowers/skills/systematic-debugging --dest ./downloads/systematic-debugging --dry-run
python3 atlas.py download obra/superpowers/skills/systematic-debugging --dest ./downloads/systematic-debugging
```

生成 ZIP：

```bash
python3 atlas.py download obra/superpowers/skills/systematic-debugging --dest ./downloads/systematic-debugging.zip --zip
```

下载器获取索引指定 commit 下的整个技能目录，以及祖先目录中的许可告示，逐个校验文件。已有目标不会被覆盖。来源、版本和下载信息记录在 `.atlas-receipt.json`。

技能也可以位于仓库根目录，例如 `python3 atlas.py show larashero3-dotcom/lieflat-less-ai-tone`。此时完整 ID 为仓库名，详情中的目录为 `.`；下载包含该版本根目录下的全部文件及许可，仍只准备文件，不运行上游脚本。

## 安装到指定目录

`install` 将文件下载到指定位置。下面的 `.agents/skills` 是目录示例，实际位置按客户端说明填写：

```bash
python3 atlas.py install obra/superpowers/skills/systematic-debugging --target ./.agents/skills/systematic-debugging
```

脚本只写入文件。技能需要的 Python 包、外部工具、MCP 服务或密钥，按其 `SKILL.md` 配置。包含父目录引用或插件根目录变量的技能，可能还需要上游插件的共享资源。

参数帮助：`python3 atlas.py --help`，或 `python3 atlas.py download --help`。
