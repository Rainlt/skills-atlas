# GitHub Pages 在线搜索

在线地址：**https://rainlt.github.io/skills-atlas/**。`browse.html` 也可通过同域名下的 `/skills-atlas/browse.html` 访问。

页面沿用仓库生成的 `browse.html`，支持中文主题搜索、名称和描述搜索、来源筛选、查看固定版本的上游目录，以及复制单项技能或 ZIP 下载命令。搜索在浏览器中完成，无需账号、后台或第三方服务。

真正下载技能时，点击页面中的“如何按需下载一个技能”，获取轻量工具包并解压，在解压目录运行卡片命令。需要 Python 3.9 或更新版本；无需克隆仓库。工具包包含 `atlas.py`、分类表、技能索引、文件指纹清单和授权说明，不包含全部上游技能正文。

## 自动发布

`.github/workflows/pages.yml` 在 `main` 的页面、打包脚本或发布配置更新后运行，也支持手动触发。目录更新 PR 合并后，生成的 `browse.html` 变化会触发发布。未合并的更新不发布到正式网页。

发布前验证所有目录指纹，然后由 `scripts/build_pages.py` 按文件白名单生成站点：

- `index.html`：首页，内容与 `browse.html` 一致。
- `browse.html`：兼容直接访问原文件名。
- `skills-atlas-tools.zip`：轻量下载工具包。
- `.nojekyll`：按静态页面发布。

GitHub Pages 的发布源设置为 **GitHub Actions**。发布工作流只读取仓库，部署任务具有 Pages 发布和身份验证所需权限，不修改源代码，也不读取个人令牌。

本地打包预览：`python3 scripts/build_pages.py --output ./_site`。修改模板后，先执行 `python3 scripts/render.py` 更新 `browse.html`。
