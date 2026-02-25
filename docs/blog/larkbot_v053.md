# ChatTool 0.5.3 | 飞书机器人：从发消息到 AI 对话

ChatTool 0.5.3 新增了完整的飞书机器人支持。本文介绍核心功能和设计思路。

---

## 为什么做飞书机器人

ChatTool 的定位是「LLM 应用开发工具箱」。之前已经有了 `Chat` 对象做多轮对话、MCP 做工具调用，但缺少一个把 AI 能力直接推送给终端用户的通道。

飞书机器人是一个理想的载体：

- 用户在熟悉的 IM 里直接和 AI 对话，零学习成本
- WebSocket 长连接模式，本地开发不需要公网服务器
- 消息类型丰富（文本、图片、文件、卡片），交互形式多样

## 架构设计

整个模块围绕三个核心类展开：

```
chattool.tools.lark
├── LarkBot         消息收发 + 事件路由
├── MessageContext  消息上下文（ctx.reply() 等快捷操作）
└── ChatSession     多用户 LLM 会话管理
```

设计原则是「简单场景极简，复杂场景可扩展」。最简示例只需 5 行：

```python
from chattool.tools.lark import LarkBot

bot = LarkBot()

@bot.on_message
def handle(ctx):
    ctx.reply(f"收到：{ctx.text}")

bot.start()
```

加上 `ChatSession` 就变成 AI 对话机器人：

```python
from chattool.tools.lark import LarkBot, ChatSession

bot = LarkBot()
session = ChatSession(system="你是一个工作助手，回答简洁专业。")

@bot.command("/clear")
def clear(ctx):
    session.clear(ctx.sender_id)
    ctx.reply("记忆已清除 ✅")

@bot.on_message
def chat(ctx):
    ctx.reply(session.chat(ctx.sender_id, ctx.text))

bot.start()
```

## 消息发送

`LarkBot` 封装了飞书 IM 的全部常用操作，避免用户直接拼 SDK 请求：

```python
bot = LarkBot()

# 文本
bot.send_text("rexwzh", "user_id", "你好")

# 图片（自动上传 + 发送）
bot.send_image_file("rexwzh", "user_id", "photo.jpg")

# 文件
bot.send_file("rexwzh", "user_id", "report.pdf")

# 富文本
bot.send_post("rexwzh", "user_id", post_content)

# 卡片
bot.send_card("rexwzh", "user_id", card_dict)

# 引用回复
bot.reply("om_message_id", "收到！")
```

图片和文件的上传之前需要手动调 SDK，现在 `send_image_file()` / `send_file()` 一步到位。

## 事件路由

通过装饰器注册消息处理器，支持指令匹配、正则匹配和兜底处理：

```python
@bot.command("/help")
def on_help(ctx):
    ctx.reply("可用指令：/help /status /clear")

@bot.regex(r"^查询\s+(.+)$")
def on_query(ctx):
    keyword = ctx._match.group(1)
    ctx.reply(f"正在查询：{keyword}")

@bot.on_message
def fallback(ctx):
    ctx.reply(f"你说了：{ctx.text}")
```

匹配优先级：`command` > `regex` > `on_message`。

## CLI 工具

不写代码也能使用。所有功能都封装成了 `chattool lark` 和 `chattool serve lark` 命令：

```bash
# 验证凭证
chattool lark info

# 查看已授权权限
chattool lark scopes -f im

# 发送消息
chattool lark send rexwzh "你好"
chattool lark send rexwzh --image photo.jpg
chattool lark send rexwzh --file report.pdf

# 上传文件（仅获取 key）
chattool lark upload photo.jpg

# 调试事件接收
chattool lark listen -l DEBUG

# 一键启动回显/AI 机器人
chattool serve lark echo
chattool serve lark ai --system "你是翻译官"
```

`chattool serve lark ai` 是最实用的命令——一行启动带多轮记忆的 AI 对话机器人。

## 踩坑记录

开发过程中遇到了几个有代表性的坑，记录在此。

### lark-oapi v1.5.3 WSClient API 变更

`lark-oapi` 的 WebSocket Client 在较新版本中不再使用 builder 模式：

```python
# 旧写法（部分文档和示例中的写法，已不兼容）
ws = WSClient.builder().app_id(...).app_secret(...).build()

# v1.5.3 正确写法
ws = WSClient(app_id=..., app_secret=..., event_handler=handler)
```

注意 `EventDispatcherHandler` 仍然使用 builder 模式，只有 `WSClient` 改了。

### WebSocket 连接成功但收不到消息

这是最常见的问题。连接日志正常（`connected to wss://...`），也有 ping/pong，但用户发消息后没有任何反应。

原因：**飞书的事件订阅不仅需要添加事件，还需要开通对应的权限。**

即使在「事件订阅」中添加了 `im.message.receive_v1`，如果没有在「权限管理」中开通「读取用户发给机器人的单聊消息」等权限，服务端不会推送任何事件。

诊断方法：

```bash
chattool serve lark echo -l DEBUG
```

如果 DEBUG 日志中只有 ping/pong，没有 `receive message`，就是权限问题。

### 修改配置后需要重新发布

在飞书开发者后台修改事件订阅、权限等配置后，需要创建新版本并提交发布，审批通过后配置才会生效。这在开发阶段容易忽略。

## 文档

完整文档见 [飞书机器人开发指南](../larkbot/index.md)：

- [飞书平台配置](../larkbot/feishu-setup.md) — 从零开始创建应用，含截图
- [快速开始](../larkbot/quickstart.md) — 5 分钟发出第一条消息
- [消息发送](../larkbot/messaging.md) — 文本、图片、文件、卡片
- [接收消息与路由](../larkbot/receiving.md) — WebSocket、指令路由
- [AI 对话集成](../larkbot/ai-chat.md) — ChatSession 多用户会话
- [交互卡片](../larkbot/cards.md) — 按钮回调、动态更新
- [命令行工具](../larkbot/cli.md) — CLI 命令速查
