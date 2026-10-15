# 更新与维护

初版已提供手动更新工作流，未开启周期任务。

在 GitHub 仓库 Actions 中选择 **Refresh catalog → Run workflow**。工作流获取白名单来源、重新分类去重，执行完整性检查和测试，有变化时提交到专用分支并创建 PR；无变化时结束。第一次使用时，仓库 Settings → Actions → General 需要允许 GitHub Actions 创建 Pull Request。默认的 `GITHUB_TOKEN` 已由 GitHub 注入，无需额外个人令牌。

后续决定周期后，在 `.github/workflows/refresh.yml` 的 `on` 中启用注释示例：

```yaml
  schedule:
    - cron: '20 1 * * 1'
```

这表示每周一 UTC 01:20，即北京时间 09:20。GitHub 调度可能延迟；公开仓库长期无活动时，平台可能停用定时工作流。手动更新和本地更新不依赖定时器。

本地更新命令见 README。更改来源前先确认它包含实际技能目录、是否改名、是否有明确的授权要求。新来源的 include 应尽量指向主目录，排除打包副本和测试样例。

`data/changes.json` 记录按完整条目 ID 的新增、移除和首选目录内容变化；来源入口切换可能同时表现为新增和移除。`data/duplicates.json` 保留完全相同内容的其他来源位置。README 和总目录计数随更新重新生成。

遇到网络失败、上游目录结构变化或校验不通过时，工作流失败，旧版本继续可用；不要通过跳过来源或禁用校验来生成“成功”结果。

GitHub Actions 仅维护索引，不自动升级用户本机的技能。不再需要的来源可从白名单移除，重新生成后审核 PR。
