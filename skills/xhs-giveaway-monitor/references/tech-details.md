# 技术细节与踩坑清单

执行监控轮之前必读。所有代码在 ZCode 内置浏览器（iab）+ mcp__node_repl__js 环境验证过。

## 1. 浏览器引导（每次 js 调用都要）

```js
const browserPluginRoot =
  process.env.ZCODE_PLUGIN_ROOT ?? process.env.CLAUDE_PLUGIN_ROOT;
const { join } = await import("node:path");
const { pathToFileURL } = await import("node:url");
const browserClientUrl = pathToFileURL(
  join(browserPluginRoot, "scripts", "browser-client.mjs"),
).href;
const { setupBrowserRuntime } = await import(browserClientUrl);
await setupBrowserRuntime({ globals: globalThis });

const browser = await agent.browsers.get("iab");
const tab = await browser.tabs.get("iab-tab:<id>");
```

⚠️ 环境变量名**必须是** `ZCODE_PLUGIN_ROOT`（fallback `CLAUDE_PLUGIN_ROOT`），模块路径是 `scripts/browser-client.mjs`。写成 `ZCODE_PLUGIN_BASE`/`ZCODE_PLUGIN_DIR` 等变体会直接报 "path undefined"。

⚠️ 单次 evaluate 有 **5 秒超时**，超时后工具返回 error，**但页面内的异步脚本会继续跑完**。两个推论：
- 长批量任务用「fire-and-poll」模式：evaluate 里启动一个写 `window.__state` 的异步循环（预期超时，catch 吞掉），然后用 Bash sleep + 轮询读取 `window.__state` 查进度。
- **绝不同时启动两个批量脚本**：两个实例并发扫描同一批目标会造成重复发送（实战踩过：同一人收到 2 条重复回复）。

## 2. 私信页（/chat）DOM 结构

| 元素 | 选择器 |
|---|---|
| 会话列表滚动容器 | `.xhs-im-conv-list__scroll` |
| 会话条目 | `.xhs-im-conv-item`，带 `data-conv-id`（= 对方 uid）和 `data-conv-kind`（`c2c`=单聊 / `group`=群聊 / `stranger-folder`=陌生人折叠夹） |
| 未读角标 | `.xhs-im-conv-item__badge`（无未读时元素不存在） |
| 昵称 / 摘要 / 时间 | `.xhs-im-conv-item__name` / `__summary-text` / `__time` |
| 陌生人折叠夹 | `data-conv-id="__stranger_folder__"`，点击后进入陌生人视图（整个列表变成仅陌生人会话） |
| 消息列表 | `.xhs-im-msg-list .chat-item` |
| 消息方向 | `.chat-item__content--left`=对方发的；`.chat-item__content--right`=自己发的（判断"是否回复过"的关键） |
| 输入框 | `.xhs-im-input-bar-editor`（contenteditable） |

### 陌生人折叠夹行为（重要）

- 小红书把**未关注你的陌生人**的私信折叠进这个夹子，主列表完全看不到。求码用户大多在这里。不做这一步会漏掉大部分求码私信。
- 回复陌生人后，会话会从陌生人视图移到主列表。
- 折叠夹条目**只在有未读时渲染**；0 未读时 DOM 里可能找不到它。入口不可见时，仍检查主列表的已读会话和已记录待办。无法通过当前页面打开的陌生人会话保留待办，汇报覆盖限制。
- 列表滚动到底后顶部条目（含折叠夹）可能被卸载，操作折叠夹前先 `scrollTop = 0` 等待再找。

### 私信发送机制

输入框是 contenteditable，无独立发送按钮，**回车即发送**：

```js
const editor = document.querySelector(".xhs-im-input-bar-editor");
editor.focus();
await sleep(300);
document.execCommand("selectAll", false, null);
document.execCommand("delete", false, null);          // 清残留
document.execCommand("insertText", false, text);       // 框架可感知的输入
await sleep(400);
editor.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", code: "Enter", keyCode: 13, which: 13, bubbles: true, cancelable: true }));
editor.dispatchEvent(new KeyboardEvent("keyup",   { key: "Enter", code: "Enter", keyCode: 13, which: 13, bubbles: true }));
await sleep(1300);
// 兜底：个别场景会弹确认按钮
const confirmBtn = Array.from(document.querySelectorAll("button")).find(b =>
  b.offsetParent !== null && /^(确定|发送|继续回复)$/.test(b.textContent.trim()));
if (confirmBtn) { confirmBtn.click(); await sleep(1200); }
```

固定目标 UID 和标签页。发码、补码和感谢语分别核对：输入前及按回车或点击确认前，校验会话 URL 的 UID、选中会话及消息区。发送前记录最后一条本人消息，发送后再次核对 UID，并验证同一会话新增的本人消息全文匹配。校验失败立即停发，记录待办并先查发码结果。

## 3. 笔记页（评论）DOM 结构

| 元素 | 选择器 |
|---|---|
| 评论滚动容器 | `.note-scroller` |
| 主评论 | `.comment-item`；子评论 `.comment-item-sub`；同线程容器 `.parent-comment` |
| 作者链接 | `.comment-item .author a[data-user-id]`（**data-user-id = 作者 uid**） |
| 回复按钮 | 评论条目内 `.interactions .reply` |
| 评论输入框 | `#content-textarea`（contenteditable `<p>`） |
| 发送按钮 | `button` 文本为「发送」，`disabled` 表示无内容 |
| 展开子回复 | 文本匹配 `/展开\s*\d*\s*条回复/` 的叶子 div/span，逐个 click |

### 评论提取要点

- **只取作者区域链接**（`.author a[data-user-id]`），评论正文里的 @提及 链接（如 @点点 官方AI）不能当作者。
- 排除自己的 uid。
- 评论列表**懒加载 + 部分虚拟化**：反复 `scrollTop = scrollHeight`（间隔 ~380ms，高度连续 3 次不变即到底）+ 点开所有「展开」按钮。
- 用户会**反复删除/恢复评论**：某轮找不到的 uid 不要写入状态文件，下轮重试；写入了就永远不会再回复他。

### 评论回复机制（与私信不同！）

点「回复」后底部输入框进入回复模式，**点「发送」按钮发送**（不是回车）：

```js
item.scrollIntoView({ block: "center" });
await sleep(600);
item.querySelector(".interactions .reply").click();
await sleep(900);
const input = document.querySelector("#content-textarea");
input.focus();
await sleep(250);
// 光标先移到末尾（回复子评论时输入框有 @提及 前缀）
document.execCommand("insertText", false, "私我～");
await sleep(450);
let sendBtn = Array.from(document.querySelectorAll("button")).find(b => b.textContent.trim() === "发送");
if (!sendBtn || sendBtn.disabled) {
  // 兜底：直接赋值 + 派发 input 事件
  input.textContent = "私我～";
  input.dispatchEvent(new InputEvent("input", { bubbles: true, data: "私我～" }));
  await sleep(450);
  sendBtn = Array.from(document.querySelectorAll("button")).find(b => b.textContent.trim() === "发送");
}
sendBtn.click();
await sleep(2500);
// 验证：该 .parent-comment 下出现自己发布的含「私我～」的子回复
```

去重预检（同一人多次评论只回一次）：

```js
const threadAlreadyReplied = (pc, uid) => {
  const mainAuthor = pc.querySelector(".comment-item .author a[data-user-id]");
  for (const sub of pc.querySelectorAll(".comment-item-sub")) {
    if (!sub.querySelector(`a[data-user-id="${MY_UID}"]`)) continue;
    if (!sub.textContent.includes("私我～")) continue;
    const nick = sub.querySelector(".content a[data-user-id]");
    if (nick ? nick.getAttribute("data-user-id") === uid
             : (mainAuthor && mainAuthor.getAttribute("data-user-id") === uid)) return true;
  }
  return false;
};
```

## 4. 页面导航与标签页踩坑

- **页面会被莫名跳转**：笔记页脚本跑到一半可能被跳回 /chat，页面内 JS 状态（window.__state）全部丢失。对策：每轮脚本控制在 ~2 分钟内；轮询时发现状态对象消失就 `tab.url()` 检查是否还在目标页，必要时重新 goto 续跑（配合去重预检，重跑不会重复发）。
- **goto 笔记页偶发不生效**（停在本页或跳回 /chat）：重试一次 goto 即可，重试前先 `tab.url()` + `tab.title()` 验证。
- **笔记链接与登录态**：
  - 先检查当前内置浏览器是否已登录；已登录就复用现有会话，不索取密码、Cookie 或会话令牌。
  - 未登录或会话过期时，请用户在已打开的浏览器窗口中自行登录；登录完成后再继续，不要尝试替用户登录。
  - 带 `xsec_token` 的完整分享链接通常可直接打开。裸笔记 URL 已实测会跳到安全验证 404，即使账号已登录也可能如此；这是链接校验问题，不代表用户未登录。
  - 裸链接打不开时，优先请用户在已登录浏览器里手动导航并点击目标笔记卡片。真实用户操作会由 SPA 生成带 token 的 URL；自动化 `.click()` 不等价，不能用它代替。
  - 如果用户手动打开笔记仍失败，再请用户提供新的完整分享链接。token 过期或安全验证出现时停止自动化，不得猜测、伪造或从隐藏状态提取 token。
  - ❌ 程序化 DOM `.click()` 点击主页卡片：404（点到的是隐藏 `<a>` 元素，非真实事件触发安全拦截）
  - ❌ CUA 真实坐标点击主页卡片：未能跳转（卡片的 `cover mask ld` 类遮罩层拦截，不可靠）
- **标签页被释放**：`tabs.get(id)` 报 unavailable 时，`browser.user.openTabs()` 找到同 URL 的条目 `claimTab` 接管；接管后可能变成 about:blank，重新 goto 即可。轮次结束后可 `tab.markHandoff()` 降低被释放概率。
- CSV / 状态文件等本地文件用 Bash 直接读写，路径放在用户目录固定位置。

## 5. 状态文件操作

```bash
# 读
python3 -c "import json;print(json.load(open('<path>'))['processedCommenters'])"
# 写（合并新 uid）
python3 << 'EOF'
import json
p = '<path>'
d = json.load(open(p))
for u in new_ok_uids:
    if u not in d["processedCommenters"]: d["processedCommenters"].append(u)
json.dump(d, open(p, 'w'), ensure_ascii=False, indent=2)
EOF
```

失败/未找到的 uid **不要**写入 processedCommenters（否则永不再重试）。

## 6. 防限流与节奏

| 场景 | 间隔 |
|---|---|
| 私信两条消息之间 | ≥2 秒 |
| 两个人之间 | ≥3 秒 |
| 两次评论回复的发送操作之间 | ≥8 秒 |
| 单轮处理上限 | 私信 15 人 / 评论 10 人 |
| 连续失败 | 3 次即熔断停止本轮，输出已成功部分 |

发送后如出现扫码验证或风控提示，立即停止本轮。
