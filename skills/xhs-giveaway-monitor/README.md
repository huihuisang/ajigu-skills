# 小红书送码监控（xhs-giveaway-monitor）

监控一篇小红书「三连/评论求码」笔记的评论区与私信，自动完成「评论引导私信 → 私信发码 → 失效补码」闭环：给新评论且未私信的用户回复「私我～」，给私信里从未回复的人发送兑换码，反馈码失效的自动补发。

## 安装

把仓库地址交给 Agent："请从 https://github.com/huihuisang/ajigu-skills 安装 xhs-giveaway-monitor。"

```bash
npx skills add huihuisang/ajigu-skills -g -y --skill xhs-giveaway-monitor
```

技能目录名和调用名均为 xhs-giveaway-monitor。也可以将完整目录复制到宿主的技能目录。

## 配置与依赖

- ZCode 内置浏览器（iab），已登录小红书网页版 www.xiaohongshu.com
- 兑换码 CSV：每行 `CODE,https://apps.apple.com/redeem?ctx=offercodes&id=<APPID>&code=CODE`，从第一行顺序取码，发送成功后删行
- 目标笔记的完整分享链接（**必须带 `xsec_token`**；实测裸 URL 和主页点击都会 404，token 过期后重新分享一次即可）
- 一个本地 JSON 状态文件，记录已评论过的用户 uid（防止重复评论）

## 使用

请求示例："监控这篇笔记，码表在 ~/Downloads/xxx.csv，感谢语是「……」。"技能执行一轮监控：

1. **私信发码**：扫描「陌生人消息」折叠夹和主列表的未读会话。从未回复过的人 → 发码 + 感谢语（用后删行）；反馈码失效/被用过的人 → 补发「给你换个新码：<CODE>」；普通致谢/表情 → 跳过并标记已读。
2. **新评论者引导**：滚动加载全部评论（含子评论），提取作者并对比状态文件；新评论且没有任何私信会话的人 → 在其评论下回复「私我～」并更新状态文件。
3. **简报**：处理人数、码号、CSV 剩余行数（<20 提醒补充）；无新内容时简短回复。

配合 ZCode 的定时任务（CronCreate，如每 30 分钟）即可持续无人值守运行；调整频率/暂停/恢复只需改 cron 表达式。

## 规则与边界

- 发送后必须验证消息/评论真实出现，失败记录并跳过，不重试不多发
- 同一人只发一个码；感谢语绝不重发；批量脚本禁止并发（防重复发送）
- CSV 只删已成功发送的行，删前后 `wc -l` 核对
- 触发验证码/滑块/风控 → 立即停止本轮并汇报；未登录 → 停止并汇报，绝不尝试登录
- 详见 [references/tech-details.md](references/tech-details.md)：全部 DOM 选择器、发送机制、导航踩坑与防限流节奏参数
