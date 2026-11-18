# Blender 技能入口

2026-11-18 按用户要求收录 [arjun988/blender-skills](https://github.com/arjun988/blender-skills)，仅增加一个 `blender-director` 总入口。原仓库 94 个专项保持独立，按当前建模、材质、动画或导出任务选择；不合成一份大说明，也不一次安装到全局。

- [总入口及专项路由](https://github.com/arjun988/blender-skills/tree/904f095d8f36a6e72adaebb08d07f884a074743d/.claude/skills/blender-director)
- [固定版本的完整技能包与共享资料](https://github.com/arjun988/blender-skills/tree/904f095d8f36a6e72adaebb08d07f884a074743d/.claude/skills)
- [Blender MCP 接入说明](https://github.com/arjun988/blender-skills/blob/904f095d8f36a6e72adaebb08d07f884a074743d/docs/BLENDER_MCP_SETUP.md)

## 已有相关项与区别

收录前以 Blender、blender-skills、三维建模及 3D 任务词检查目录，没有检到 Blender 专项入口；少量相关候选核对如下。

| 入口 | 用途 | 与本次关系 |
|---|---|---|
| [3d-web-experience](https://github.com/sickn33/agentic-awesome-skills/tree/a3072641b750a1fb2f6ce695a5f984ea3d4c3ec1/skills/3d-web-experience) | 用 Three.js、React Three Fiber、Spline 制作或排查三维网页 | 网页实现，不能代替 Blender 建模执行 |
| [3d-games](https://github.com/sickn33/agentic-awesome-skills/tree/a3072641b750a1fb2f6ce695a5f984ea3d4c3ec1/skills/game-development/3d-games) | 三维游戏中的渲染、着色器、物理、相机原则 | 游戏开发指导，不是 Blender 操作连接 |
| blender-director | 在 Blender 中按任务组织建模、材质、镜头、动画与导出 | 独立用途入口，保留上述旧项，不作同用途合并 |

## 使用与下载边界

例如“根据参考图制作钟楼，调整材质和灯光，导出模型”，可从总入口选相应专项；需要与正在运行的 Blender 交互时，另核对 BlenderMCP 插件、客户端连接与版本条件。源项目声明支持 Codex 等客户端，本次没有安装、接入或真实建模验证。Skill 包采用 MIT；外部生成、素材服务和模型费用按实际任务另核对，不自动配置 API Key。

Atlas 的单项下载只包含 `blender-director` 目录内的 `SKILL.md`、内部路由参考及祖先许可证，**不包含同级共享 `references/` 和其余专项**。下载总入口不能当作完整可运行组合；实际使用从上面的固定完整目录取所需配套。索引保留原说明和目录指纹，不重写或删减上游正文。

核对范围：固定版本的总入口、内部路由参考、MCP 接入说明、MIT 许可证四份文件已按 Git blob 核验；没有执行上游程序。94 项数量来自固定目录树，不表示逐项审阅或全部可用。收录状态为“用途与结构已核对”，未进入通用精选，也未替换动画工具箱默认路线。
