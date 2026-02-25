# 快速开始

5 分钟内让机器人发出第一条消息，并接收用户回复。

## 前置条件

完成 [飞书平台配置](feishu-setup.md) 中的前 5 步，确保：

- [x] 已创建企业自建应用，获得 App ID 和 App Secret
- [x] 已开启机器人能力
- [x] 已申请 `im:message` 权限
- [x] 已在「事件订阅」中选择「长连接接收事件」，并订阅 `im.message.receive_v1`

## 1. 安装

```bash
pip install "chattool[tools]"
```

## 2. 配置凭证

在项目根目录创建 `.env` 文件（或直接设置环境变量）：

```bash title=".env"
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## 3. 发送第一条消息

=== "CLI"

    ```bash
    chattool lark send rexwzh "👋 你好，这是来自 chattool 的第一条消息！"
    ```

=== "Python"

    ```python title="send_hello.py"
    from dotenv import load_dotenv
    load_dotenv()

    from chattool.tools.lark import LarkBot

    bot = LarkBot()

    resp = bot.send_text("rexwzh", "user_id", "👋 你好，这是来自 chattool 的第一条消息！")

    if resp.success():
        print(f"✅ 发送成功，message_id = {resp.data.message_id}")
    else:
        print(f"❌ 发送失败: code={resp.code}, msg={resp.msg}")
    ```

    ```bash
    python send_hello.py
    ```

!!! tip "快速验证凭证"
    运行 `chattool lark info` 可验证 App ID / Secret 是否正确。

## 4. 接收用户消息并回复

```python title="echo_bot.py"
from dotenv import load_dotenv
load_dotenv()

from chattool.tools.lark import LarkBot

bot = LarkBot()

@bot.on_message
def handle(ctx):
    """把用户发的内容原样回复"""
    print(f"收到消息: {ctx.text!r} from {ctx.sender_id}")
    ctx.reply(f"收到你说的：{ctx.text}")

# WebSocket 长连接模式，无需公网服务器
bot.start()
```

运行后，在飞书给机器人发消息，它会自动回复。

## 5. 加入指令路由

```python title="bot_with_commands.py"
from dotenv import load_dotenv
load_dotenv()

from chattool.tools.lark import LarkBot

bot = LarkBot()

@bot.command("/help")
def on_help(ctx):
    ctx.reply(
        "📖 可用指令：\n"
        "  /help   — 显示帮助\n"
        "  /status — 查看运行状态\n\n"
        "直接发消息，机器人会原样回复。"
    )

@bot.command("/status")
def on_status(ctx):
    import time
    ctx.reply(f"✅ 运行正常 | {time.strftime('%H:%M:%S')}")

@bot.on_message          # 兜底：未匹配任何指令的消息
def echo(ctx):
    ctx.reply(f"你说：{ctx.text}\n（发送 /help 查看指令）")

bot.start()
```

## 6. 接入 AI 对话

只需 10 行代码，机器人就能用大语言模型回复：

```python title="ai_bot.py"
from dotenv import load_dotenv
load_dotenv()  # 同时需要 OPENAI_API_KEY

from chattool.tools.lark import LarkBot, ChatSession

bot = LarkBot()
session = ChatSession(system="你是一个工作助手，回答简洁专业。")

@bot.command("/clear")
def clear(ctx):
    session.clear(ctx.sender_id)
    ctx.reply("✅ 对话记忆已清除")

@bot.on_message
def chat(ctx):
    reply = session.chat(ctx.sender_id, ctx.text)
    ctx.reply(reply)

bot.start()
```

!!! tip "不写代码？用 CLI"
    上面的回显机器人和 AI 机器人都可以用一条命令启动：

    ```bash
    chattool serve lark echo     # 回显机器人
    chattool serve lark ai       # AI 对话机器人
    ```

    详见 [命令行工具](cli.md)。

## 接下来

| 目标 | 文档 |
|------|------|
| 了解所有发送消息的方式 | [消息发送](messaging.md) |
| 深入了解事件路由 | [接收消息与路由](receiving.md) |
| AI 会话管理进阶 | [AI 对话集成](ai-chat.md) |
| 发送卡片和处理按钮 | [交互卡片](cards.md) |
| 命令行一键操作 | [命令行工具](cli.md) |
| 飞书平台详细配置 | [飞书平台配置](feishu-setup.md) |
