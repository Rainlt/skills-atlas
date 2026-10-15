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

中文词会按主题扩展匹配，分类和关键词见 [taxonomy.json](../taxonomy.json)。搜索结果中的 ID 包含仓库和技能路径；重名技能可以据此区分。

## 查看与下载

`show` 显示来源、固定版本、许可声明和环境要求。`--dry-run` 预览文件数量等信息，不下载文件。

```bash
python3 atlas.py show obra/superpowers/skills/systematic-debugging
python3 atlas.py download obra/superpowers/skills/systematic-debugging --dest ./downloads/systematic-debugging --dry-run
python3 atlas.py download obra/superpowers/skills/systematic-debugging --dest ./downloads/systematic-debugging
```

生成 ZIP：

```bash
python3 atlas.py download obra/superpowers/skills/systematic-debugging --dest ./downloads/systematic-debugging.zip --zip
```

下载器获取索引指定 commit 下的整个技能目录，以及祖先目录中的许可告示，逐个校验文件。已有目标不会被覆盖。来源、版本和下载信息记录在 `.atlas-receipt.json`。

## 安装到指定目录

`install` 将文件下载到指定位置。下面的 `.agents/skills` 是目录示例，实际位置按客户端说明填写：

```bash
python3 atlas.py install obra/superpowers/skills/systematic-debugging --target ./.agents/skills/systematic-debugging
```

脚本只写入文件。技能需要的 Python 包、外部工具、MCP 服务或密钥，按其 `SKILL.md` 配置。包含父目录引用或插件根目录变量的技能，可能还需要上游插件的共享资源。

参数帮助：`python3 atlas.py --help`，或 `python3 atlas.py download --help`。
