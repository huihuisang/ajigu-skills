# 项目代理指令模板

把[根模板](AGENTS.template.md)复制为新项目的根目录 `AGENTS.md`，或将适用规则合并到现有入口。模板可以直接使用。项目有明确的范围、目标和验证命令时，再写入对应章节。

将适用的指南复制到目标仓库的 `.agents/guides/`，把对应入口加入根文件的「按任务阅读」。如果仓库已有权威指南，将适用规则并入原文并链接到那里。

| 复制指南 | 何时读取 | 根入口使用的链接 |
| --- | --- | --- |
| [Apple 应用](guides/apple-app.md) | Apple 构建、模拟器或真机验证、本地化、签名 | `[Apple 应用流程](.agents/guides/apple-app.md)` |
| [Web 应用](guides/web-app.md) | 网站界面、浏览器验证、SEO、公开构建产物 | `[Web 应用流程](.agents/guides/web-app.md)` |
| [发布与数据](guides/release-and-data.md) | 发布、部署、凭据、持久化和迁移 | `[发布与数据流程](.agents/guides/release-and-data.md)` |

- 根入口保留影响日常操作的约束、受影响目标的验证入口，以及不可跳过的权限门槛。
- 给每条阅读入口写清任务、路径或操作条件。普通 Markdown 链接由代理在任务匹配时打开。子目录的 `AGENTS.md` 只补充局部规则。
- 优先复用 README、设计决策、脚本和已有技能。使用 Claude Code 的项目可在 `CLAUDE.md` 通过 `@AGENTS.md` 共用根入口。
- 逐项核实项目路径、scheme、支持语言和命令。机器专用路径、凭据、私有证据和个人通知设置留在本机。用新会话确认指令加载。

[AGENTS.md 加载说明](https://learn.chatgpt.com/docs/agent-configuration/agents-md) · [技能加载说明](https://learn.chatgpt.com/docs/build-skills)
