# 更新与维护

已开启每周更新：**每周一北京时间 09:20（UTC 01:20）**，通过 GitHub Actions 的 **Refresh catalog** 执行。

工作流先独立搜索新来源，按预算核实候选和历史队列，再获取白名单来源、重新分类去重，执行完整性检查和测试。有变化时提交到专用分支并创建 PR；PR 由维护者审核和合并，不自动合并。也可以在仓库 Actions 中选择 **Refresh catalog → Run workflow** 随时手动检查。默认的 `GITHUB_TOKEN` 由 GitHub 注入，无需额外个人令牌；仓库已允许 GitHub Actions 创建 Pull Request。

## 发现新来源

`discovery.json` 保存通用检索式与预算，独立于 `sources.json`。搜索覆盖 Agent Skills 主题、科研技能、长任务与长期目标；名称与简介查询用于减少大型 README 合集造成的干扰。它是有边界的抽样，不代表搜索了全部 GitHub。可继续补充主题查询，无需修改代码。

```bash
python3 scripts/discover.py
```

每条查询默认读取按 star 排序的前 20 个结果，各查询轮流选取候选，共核实 16 个；另按最久未检查的顺序核实 4 个历史候选。请求较多，建议通过 `GITHUB_TOKEN` 环境变量使用 GitHub API 配额。网络或搜索失败时失败退出，保留上次报告；个别候选核实失败时记录错误并以非零状态退出，定时任务不会据此提交“全部成功”的 PR。

候选核实读取固定 commit 的完整目录树，寻找实际 `SKILL.md`，优先抽样主 `skills/` 目录中的 3 份说明并校验 Git blob 指纹。截断树、篡改内容、缺失说明和网络错误分别记录，README 链接本身不算技能证据。说明只解析为数据，不执行上游指令。

- `data/discovery-queue.json`：合并搜索与合集链接的持久候选队列，保留来源、commit、抽样和核实状态。
- `data/discovery-report.json`：本次查询、返回排名、检查范围与错误。
- `docs/DISCOVERY.md`：供审核者阅读的报告。

`verified_candidate` 表示已确认存在技能文件和有效说明抽样，不表示所有技能质量、许可或运行兼容性都已验证。审核后才将来源加入 `sources.json`；有运行时或共享资源依赖的来源，应填写 `compatibility`。该提示会进入技能详情、网页和下载回执，单独下载目录不等于安装完整系统。

可用 `--require-repo owner/repo` 做发现验收：它要求该仓库本次被通用查询命中并成功核实，不会将参数作为搜索词或候选种子。用于验收的仓库应尚未列入来源白名单；已收录项目由正常索引流程验证。离线单元测试不冒充在线搜索验收。

周期配置位于 `.github/workflows/refresh.yml`：

```yaml
  schedule:
    - cron: '20 1 * * 1'
```

这表示每周一 UTC 01:20，即北京时间 09:20。GitHub 调度可能延迟；公开仓库长期无活动时，平台可能停用定时工作流。手动更新和本地更新不依赖定时器。

## 本地更新

需要 Git、Python 3.9+ 和 PyYAML。在仓库目录运行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
python3 scripts/discover.py
python3 scripts/update.py
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
```

Windows PowerShell 将激活命令改为 `.venv\Scripts\Activate.ps1`。

首次更新需要读取数千份技能说明。说明文件按内容指纹缓存，后续只获取变化的文件。已有完整缓存时，可用 `python3 scripts/update.py --offline` 重新分类和生成目录。

更改来源前先确认它包含实际技能目录、是否改名、是否有明确的授权要求。新来源的 include 应尽量指向主目录，排除打包副本和测试样例。

`data/changes.json` 记录按完整条目 ID 的新增、移除和首选目录内容变化；来源入口切换可能同时表现为新增和移除。`data/duplicates.json` 保留完全相同内容的其他来源位置。README 和总目录计数随更新重新生成。

遇到网络失败、上游目录结构变化或校验不通过时，工作流失败，旧版本继续可用；不要通过跳过来源或禁用校验来生成“成功”结果。

GitHub Actions 仅维护索引，不自动升级用户本机的技能。不再需要的来源可从白名单移除，重新生成后审核 PR。
