# Skills Atlas · 技能导航

把分散在多个公开仓库中的 Agent Skills 归类、去重，保留来源，只下载你选中的技能。

<!-- STATS:START -->
**12 个来源 · 3946 个独立技能目录 · 避开 5226 处分发副本 · 17 个中文主题**

索引快照：`f03a82e7ea5d088a`。主目录之间完全相同的条目合并 0 处；同名但不同实现均保留。
<!-- STATS:END -->

**从这里开始：[中文分类目录](CATALOG.md) · [来源与版本](docs/SOURCES.md) · [整理规则](docs/METHODOLOGY.md) · [质量记录](docs/QUALITY.md)**

本仓库保存元数据、目录和工具，不收集整套技能正文。中文分类和搜索词由本项目维护，技能名称和描述保留上游原文。它是有明确来源范围的导航，不宣称覆盖全部互联网技能。

## 查找技能

无需运行工具时，直接打开上面的分类目录。下载本仓库后，双击 `browse.html` 即可离线搜索、筛选来源并复制单项下载命令；页面无需账号或后台。

命令行需要 Python 3.9 或更新版本，搜索和下载无需安装第三方包：

```bash
git clone https://github.com/Rainlt/skills-atlas.git
cd skills-atlas
python3 atlas.py search '科研'
python3 atlas.py search 'pdf' --source anthropics
python3 atlas.py search 'debug' --category testing
python3 atlas.py search '视频' --limit 10
```

搜索支持名称、用途、分类、来源筛选。中文词按主题扩展，并不等同于语义搜索或完整中文翻译。分类为规则初分，可通过 `taxonomy.json` 纠正。

## 只下载一个技能

用搜索结果中的完整 ID 查看来源、许可声明、兼容性和资源依赖线索：

```bash
python3 atlas.py show anthropics/skills/skills/pdf
python3 atlas.py download anthropics/skills/skills/pdf --dest ./downloads/pdf --dry-run
python3 atlas.py download anthropics/skills/skills/pdf --dest ./downloads/pdf
```

也可以生成适合转移或手动导入的 ZIP：

```bash
python3 atlas.py download anthropics/skills/skills/pdf --dest ./downloads/pdf.zip --zip
```

这里的 `pdf` 仅用于演示检索和下载；它的许可在上游单独声明，不能因为仓库公开就推断为宽松开源。

下载只请求该技能目录内的文件及祖先层级的许可告示，不克隆全部上游库。版本固定到索引记录的完整 commit，逐个校验 Git blob SHA，并校验文件清单与 Git 目录指纹一致。脚本不会自动执行技能、安装依赖或覆盖现有目录。

## 使用下载的技能

先检查 `SKILL.md` 中的环境和工具要求。对于支持目录式 Agent Skills 的客户端，可写入你明确选择的技能目录：

```bash
# .agents/skills 是通用目录示例；实际位置请遵循你的客户端说明。
python3 atlas.py install anthropics/skills/skills/pdf --target ./.agents/skills/pdf
```

`install` 和下载使用相同的校验流程；它只复制文件，不注册插件、不安装外部服务、不承诺所有客户端即装即用。含插件根目录变量、父目录引用、外部 MCP、密钥或专用运行环境的技能，可能需要按上游说明补充配置。重名技能必须用完整 ID 选择实现。

## 更新索引

用户查找和下载不需要 GitHub 凭据。维护索引需要 Git、Python 和 PyYAML：

```bash
python3 -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell 改为：.venv\Scripts\Activate.ps1
python3 -m pip install -r requirements-dev.txt
python3 scripts/update.py
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
```

更新器只取 Git 提交和目录对象，再按需获取技能说明，用于读取元数据与计算指纹；不会下载完整上游技能库。文件按内容指纹缓存，未变化的说明无需重新获取。任何一个来源失败，保留原有索引，不发布缺项快照。首次生成会请求数千份说明，耗时取决于网络；后续通常只获取变更项。

Actions 的 **Refresh catalog** 每周一北京时间 **09:20** 自动检查，也支持手动运行。成功验证后，有变化则创建更新分支和 Pull Request，供维护者审核；无变化则结束。PR 不自动合并。详见[更新说明](docs/UPDATES.md)。索引更新不会替换用户已经下载的技能。

## 项目文件

| 文件 | 作用 |
|---|---|
| `sources.json` | 允许扫描的来源、目录和来源优先级 |
| `taxonomy.json` | 中文主题、英文关键词和中文搜索词 |
| `data/catalog.json` | 去重后的技能元数据、来源和固定版本 |
| `data/manifests.json` | 每个完整技能目录的文件指纹，用于单项下载 |
| `data/duplicates.json` | 完全重复、同名版本、说明相同但资源不同的关系 |
| `data/discovery-queue.json` | 在集合 README 中发现、尚未验证的其他仓库 |
| `data/changes.json` | 最近一次快照与上次相比的增加、移除和内容更新 |
| `browse.html` | 可离线打开的中文搜索界面 |

## 来源与授权

最初的来源包含用户提出的 [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) 和 [sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills)，并扩充了 Anthropic、OpenAI、Vercel、Hugging Face、Google Gemini、Supabase、Remotion、Superpowers、Trail of Bits 和 K-Dense 的技能。完整快照及署名见 [SOURCES](docs/SOURCES.md)。格式参考 [Agent Skills 规范](https://agentskills.io/specification)。

本项目原创工具和说明采用 [MIT](LICENSE)。第三方技能及其元数据的权利归原作者，受各自许可证约束；本项目许可证不重新授权第三方内容。仓库级许可证、技能级声明、许可证文件和来源引用分别保留。许可未确认的条目会明确标记，且收录不代表质量、安全或兼容性认证。

欢迎通过 Issue / Pull Request 补充来源、纠正分类和授权信息。新增来源应先验证实际 `SKILL.md` 目录、授权和更新方式，再加入白名单。
