# app-icon-studio

## 有什么用

把产品描述或参考图变成 macOS、iOS 应用图标。默认输出直角正方形源图，附提示词和检查记录；需要继续编辑时可准备透明前景素材。

它固定了容易反复出错的画布规范，并把完整图片与真正分层素材分开。默认保留可爱玩具质感，也支持明确指定的其他风格。适合应用图标，不用于工具栏符号或批量图标套装。

## 安装

把仓库地址交给 Agent：“请从 https://github.com/huihuisang/ajigu-skills 安装 app-icon-studio。”

也可以使用 Skills CLI，只安装这一项：

```bash
npx skills add huihuisang/ajigu-skills -g -y --skill app-icon-studio
```

命令安装需要 Node.js 与网络；它们不是提示词脚本的运行依赖。也可以把仓库中的 `skills/app-icon-studio` 完整目录复制或链接到宿主支持的 Skill 搜索目录，再重新加载 Skill 列表。

## 配置

无需额外配置或单独提供 API Key。复用宿主已经配置的图像生成和编辑能力。没有这项能力时，只能输出提示词，不能生成图片。

## 使用

- “给我的睡眠 App 生成一个图标，柔软纸张质感，方便放进 Icon Composer。”
- “用 app-icon-studio，根据这张参考图生成直角正方形图标。”
- “把这个 App 图标做成独立透明前景，方便修改背景。”
- “只帮我写 App 图标提示词，先不出图。”

## 兼容性与依赖

提示词组装使用 Python 3.10+ 标准库。PNG 像素检查另需 Pillow；优先使用已有环境。只有进行原生导入时才需要 macOS 与 Icon Composer，日常出图不依赖该应用。

脚本已在 macOS 的 Python 3.12 / Pillow 12.3 环境执行；Windows、Linux 未实机验证。没有浏览器、GUI 或子 Agent 仍可组装提示词；图片生成取决于宿主，离线时只支持本地组装与检查。

程序测试和静态校验不证明所有宿主都会正确触发，也不证明图像审美质量。此交付未做图像生成对照实验或真实 Icon Composer 导入测试。

## 数据与适用边界

本地脚本不联网、不读取凭据、不改动源图片。图像生成或编辑时，提示词及所选参考图会传给宿主已配置的图像服务，遵循该服务的权限和费用规则；未经授权不另接外部服务。

不自动发布、提交审核或替换应用资源。完整 PNG 不是可独立调整背景和主体的分层工程。本 Skill 不自带 `.icon` 序列化器；原生工程需通过本机应用或已验证的适配器另行完成。

参考 [app-icon-skill](https://github.com/xzhih/app-icon-skill) 的素材与验证流程，独立编写实现，未复制其代码或模板。分层规范的官方来源见 [Icon Composer 素材规范](references/icon-composer.md)。

## 输出

每次使用独立输出目录，包含最终 PNG、结构化设计描述、提示词与检查记录。可选前景图与预览另存。具体路径沿用当前项目或宿主的交付约定，不把生成结果写入 Skill 安装目录。

## 测试

运行方法见 [输入与命令](references/commands.md)。脚本回归覆盖画布、透明度、错误输入、损坏图片和已有文件保护；[触发样例](tests/trigger-cases.json) 用于独立检查请求边界。
