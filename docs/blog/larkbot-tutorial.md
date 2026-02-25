# 飞书机器人开发全攻略 (LarkBot Tutorial)

本教程旨在帮助开发者快速掌握如何使用 `chattool` 构建功能丰富的飞书（Lark）机器人。我们将从基础配置开始，逐步深入到 AI 对话、交互卡片和生产环境部署。

---

## 1. 简介与核心架构

`chattool.tools.lark` 模块集成了 `lark-oapi`，为开发者提供了极简的接口来操作飞书机器人。

### 核心组件
- **[LarkBot](../larkbot/index.md)**：核心类，负责连接、发送消息、路由事件。
- **[MessageContext](../larkbot/receiving.md)**：消息上下文，封装了快捷回复（`ctx.reply()`）和发送者信息。
- **[ChatSession](../larkbot/ai-chat.md)**：多用户会话管理器，轻松集成大语言模型（LLM）。

---

## 2. 飞书平台配置快速指南

在开始编写代码前，你需要在 [飞书开放平台](https://open.feishu.cn/) 完成以下准备工作。

> 详细步骤请参考：[飞书平台配置教程](../larkbot/feishu-setup.md)

### 第一步：创建应用
登录开发者后台，点击「**创建企业自建应用**」，填写应用名称（如 `AI 助手`）。

![创建企业自建应用](https://qiniu.wzhecnu.cn/FileBed/source/20260226020952.png)

### 第二步：获取凭证
进入「凭证与基础信息」，获取 **App ID** 和 **App Secret**。

![凭证与基础信息](https://qiniu.wzhecnu.cn/FileBed/source/20260226021130.png)

### 第三步：开启机器人能力
在「应用功能」→「机器人」中，开启机器人开关。

![开启机器人能力](https://qiniu.wzhecnu.cn/FileBed/source/20260226024745.png)

### 第四步：申请权限
在「权限管理」中申请以下权限：
- `im:message`（发送消息）
- `im:message.receive_v1`（接收消息事件）
- `contact:user.employee_id:readonly`（如需使用 `user_id` 发送）

![权限管理](https://qiniu.wzhecnu.cn/FileBed/source/20260226024831.png)

### 第五步：配置事件订阅
在「事件订阅与回调」中：
1. 选择 **「使用长连接接收事件」**（WebSocket 模式），无需公网 IP 即可本地调试。
2. 添加订阅事件：`接收消息 v2.0` (`im.message.receive_v1`)。

![选择长连接接收事件](https://qiniu.wzhecnu.cn/FileBed/source/20260226030553.png)

### 第六步：发布应用
创建版本并申请发布，确保权限和订阅生效。

![创建版本并提交发布](https://qiniu.wzhecnu.cn/FileBed/source/20260226031345.png)

---

## 3. 快速上手

### 安装
```bash
pip install "chattool[tools]"
```

### 配置环境变量
在项目根目录创建 `.env` 文件：
```bash
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Hello World 机器人
只需几行代码，即可实现一个原样回显消息的机器人：

```python
from chattool.tools.lark import LarkBot

bot = LarkBot() # 自动读取环境变量

@bot.on_message
def handle_echo(ctx):
    """回显用户发送的内容"""
    ctx.reply(f"你说了：{ctx.text}")

# 启动长连接监听
bot.start()
```

---

## 4. 消息路由与指令

你可以使用装饰器轻松地将不同消息分发到特定的处理函数。

### 指令路由 (`@bot.command`)
匹配以 `/` 开头的指令，优先级最高。
```python
@bot.command("/help")
def on_help(ctx):
    ctx.reply("📖 这是一个 AI 助手，你可以直接和我对话。")
```

### 正则路由 (`@bot.regex`)
```python
@bot.regex(r"^查询\s+(.+)$")
def on_query(ctx):
    keyword = ctx._match.group(1)
    ctx.reply(f"🔍 正在为你查询：{keyword}")
```

### 兜底处理器 (`@bot.on_message`)
```python
@bot.on_message(private_only=True)
def handle_private(ctx):
    ctx.reply("这是私聊消息处理器")
```

---

## 5. 发送多样化消息

`LarkBot` 支持发送文本、富文本、图片、文件等。

-   **文本消息**：`bot.send_text(receive_id, "user_id", "内容")`
-   **富文本**：支持标题、超链接、代码块等。使用 `bot.send_post()`。
-   **图片/文件**：
    ```python
    bot.send_image_file("rexwzh", "user_id", "image.jpg")
    bot.send_file("rexwzh", "user_id", "report.pdf")
    ```

> 详情参考：[消息发送指南](../larkbot/messaging.md)

---

## 6. AI 对话集成

结合 `ChatSession`，你可以快速赋予机器人智能对话能力。

```python
from chattool.tools.lark import LarkBot, ChatSession

bot = LarkBot()
session = ChatSession(system="你是一个专业的编程助手，请用简洁的代码回答问题。")

@bot.on_message
def ai_chat(ctx):
    # 为每个用户维护独立会话
    reply = session.chat(ctx.sender_id, ctx.text)
    ctx.reply(reply)

bot.start()
```

-   **多用户隔离**：每个用户拥有独立的上下文。
-   **历史限制**：通过 `max_history` 防止 token 消耗过大。

> 详情参考：[AI 对话集成](../larkbot/ai-chat.md)

---

## 7. 交互式卡片

卡片可以提供按钮、下拉框等交互控件，极大地提升用户体验。

### 发送卡片
```python
card = {
    "header": {"title": {"tag": "plain_text", "content": "任务提醒"}, "template": "blue"},
    "elements": [
        {"tag": "div", "text": {"tag": "lark_md", "content": "**任务**：完成周报"}},
        {
            "tag": "action",
            "actions": [
                {"tag": "button", "text": {"tag": "plain_text", "content": "完成"}, "value": {"action": "done"}}
            ]
        }
    ]
}
bot.send_card("rexwzh", "user_id", card)
```

### 处理回调
```python
@bot.card_action("done")
def on_card_done(ctx):
    ctx.update_card({"header": {"title": {"tag": "plain_text", "content": "任务已完成"}, "template": "green"}})
    ctx.toast("标记成功！", type="success")
```

> 详情参考：[交互卡片深度指南](../larkbot/cards.md)

---

## 8. 命令行工具 (CLI)

`chattool` 提供了强大的 CLI 命令，甚至不需要写代码就能启动机器人：

-   **验证凭证**：`chattool lark info`
-   **一键启动 AI 机器人**：
    ```bash
    chattool serve lark ai --system "你是一个翻译官"
    ```
-   **发送测试消息**：`chattool lark send rexwzh "测试消息"`
-   **监听调试**：`chattool lark listen -l DEBUG`

> 详情参考：[命令行工具手册](../larkbot/cli.md)

---

## 9. 生产环境部署

在生产环境中，建议从 WebSocket 切换到 **Webhook (Flask/FastAPI) 模式** 以获得更好的稳定性。

```python
bot.start(
    mode="flask",
    encrypt_key="...",
    verification_token="...",
    port=8080
)
```

> 更多部署细节见：[接收消息与路由 - Webhook 模式](../larkbot/receiving.md)
