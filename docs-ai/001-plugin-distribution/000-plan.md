# 方案：双宿主插件整包分发

状态：已定稿

## 背景与目标

仓库已有 11 个独立技能，采用 skills/<name>/SKILL.md 结构。增加 Codex 和 Claude Code 插件整包入口，继续支持 Skills CLI 单项安装；技能源码保持一份。

用户已明确授权按此方案实施、验证并推送。发布对象为当前仓库的 main 分支，不提交官方插件目录审核，不改动用户实际安装配置。

## 设计与取舍

- 仓库根目录作为插件根目录，初始版本为 0.1.0。
- 拟新增根目录 plugin.json，采用 Agent Plugins 清单；Claude 使用拟新增 .claude-plugin/plugin.json。
- 拟新增 .agents/plugins/marketplace.json 与 .claude-plugin/marketplace.json，两者均提供 ajigu-skills 整包并引用仓库根目录。
- 若本机 Codex CLI 的实际安装不支持通用清单，则增加 .codex-plugin/plugin.json 兼容入口并在测试中约束元数据一致。
- 保留现有 skills 目录及单项安装命令。增加真实 CLI 隔离安装检查，不自动删除旧的独立技能。
- 不增加 MCP、hook、服务认证、自动依赖安装或全局指令注入。task-artifacts 命令仍由用户显式初始化。

备选为分成多个主题插件或复制两份技能源码。目前规模不需要额外拆包，复制源码会带来同步成本，因此不采用。

## 验收与验证

| 编号 | 验收标准 | 必要验证条件 | 方法与证据 |
| --- | --- | --- | --- |
| AC-01 | 插件及 marketplace 清单一致，源码仅一份 | 必须 | 静态回归检查、官方 CLI 校验、资源清单比较 |
| AC-02 | Codex 可添加 marketplace 并安装整包，包含全部 11 项 | 必须 | 隔离 HOME/CODEX_HOME，实际 CLI 安装与缓存内容核对 |
| AC-03 | Claude 可添加 marketplace 并安装整包，加载全部 11 项 | 必须 | 隔离 HOME/CLAUDE_CONFIG_DIR，实际 CLI 安装与组件清单 |
| AC-04 | Skills CLI 仍可独立安装一个技能 | 必须 | 隔离用户目录安装 write-ai-doc，确认未安装整包 |
| AC-05 | 使用说明覆盖整包、单项、更新、去重及工具初始化 | 必须 | README 核对，命令与实际 CLI 流程一致 |
| AC-06 | 发布文件与必要验证匹配，远端包含最终提交 | 必须 | 内容摘要、jj 推送、远端引用与树核对 |

测试只验证清单分发、安装与组件加载，不执行技能中的磁盘清理、签名、公证或外部服务调用。桌面插件目录的视觉交互和其他系统不属于本次验收。

## 审核要求

完成后对固定版本执行独立 Standards 与 Spec 审核，覆盖安装隔离、路径约束、单份源码和验收证据。审核结论与对应版本一起记录；必要检查失败时不得报告完成。

## 官方依据

核查日期：2026-10-27。

- [OpenAI 插件打包](https://developers.openai.com/plugins/build/plugins)：通用清单、兼容入口、marketplace 与插件根目录。
- [Claude 插件清单](https://code.claude.com/docs/en/plugins-reference)：清单与默认组件目录。
- [Claude marketplace](https://code.claude.com/docs/en/plugin-marketplaces)：仓库目录、相对来源、注册和安装流程。

## 待确定事项

无。两端 CLI 的实际支持差异在实现验证中处理，不改变技能范围和安装授权。
