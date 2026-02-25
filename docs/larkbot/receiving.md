# 接收消息与路由

本章介绍如何接收用户消息，以及如何通过装饰器将不同类型的消息路由到对应处理函数。

---

## 两种事件接收模式

### WebSocket 长连接（推荐本地开发）

SDK 主动连接飞书服务器，无需公网 URL。

**飞书平台配置：** 「事件订阅」→「使用长连接接收事件」

```python
bot.start()          # 默认 WebSocket
bot.start(mode="ws") # 显式指定
```

在 Jupyter Notebook 或脚本中非阻塞运行：

```python
thread = bot.start_background()
print("机器人已在后台启动")
```

### Webhook（生产环境）

飞书平台推送 HTTP POST 到你的服务器。

**飞书平台配置：** 「事件订阅」→「将事件发送至开发者服务器」→ 填写请求 URL

```python
bot.start(
    mode="flask",
    encrypt_key="your_encrypt_key",
    verification_token="your_verification_token",
    host="0.0.0.0",
    port=7777,
    path="/webhook/event",
)
```

也可以手动集成到现有 FastAPI / Django 项目：

=== "FastAPI"

    ```python
    from fastapi import FastAPI, Request
    from lark_oapi.adapter.fastapi import parse_req, parse_resp

    app = FastAPI()
    event_handler = bot._build_event_handler("encrypt_key", "verify_token")

    @app.post("/webhook/event")
    async def webhook(request: Request):
        req = await parse_req(request)
        resp = event_handler.do(req)
        return parse_resp(resp)
    ```

=== "Flask"

    ```python
    from flask import Flask
    from lark_oapi.adapter.flask import parse_req, parse_resp

    app = Flask(__name__)
    event_handler = bot._build_event_handler("encrypt_key", "verify_token")

    @app.route("/webhook/event", methods=["POST"])
    def webhook():
        return parse_resp(event_handler.do(parse_req()))
    ```

---

## MessageContext — 消息上下文

处理函数收到的 `ctx` 对象封装了所有消息信息：

```python
@bot.on_message
def handle(ctx):
    # 消息内容
    ctx.text        # str：消息文字（非文本类型返回空串）
    ctx.msg_type    # str：text / image / file / interactive / post / ...
    ctx.message_id  # str：消息 ID（om_xxx）
    
    # 发送者
    ctx.sender_id   # str：发送者 open_id
    ctx.sender_type # str：user / bot
    
    # 会话信息
    ctx.chat_id     # str：群 chat_id 或私聊 open_id
    ctx.chat_type   # str：group / p2p
    ctx.is_group    # bool：是否群聊
    ctx.thread_id   # str | None：话题 ID
    
    # 原始事件（完整数据）
    ctx.raw
    
    # 解析 content 为 dict
    ctx.get_content()
```

### 快捷回复方法

```python
ctx.reply("回复文本")           # 引用回复，文本
ctx.reply_card(card_dict)      # 引用回复，卡片
ctx.send("发新消息")            # 向同会话发新消息（不引用）
ctx.send_card(card_dict)       # 向同会话发卡片（不引用）
```

---

## 装饰器路由

### @bot.on_message — 兜底处理器

```python
@bot.on_message
def handle_all(ctx):
    """处理所有未被其他路由匹配的消息"""
    ctx.reply(f"收到：{ctx.text}")
```

#### 过滤群聊/私聊

```python
@bot.on_message(group_only=True)
def group_handler(ctx):
    """只处理群聊消息"""
    ctx.reply(f"收到群消息 @{ctx.sender_id}")

@bot.on_message(private_only=True)
def private_handler(ctx):
    """只处理私聊消息"""
    ctx.reply("你好，有什么可以帮你？")
```

### @bot.command — 指令路由

匹配以 `/` 开头的指令文本（大小写不敏感）。指令优先级高于 `on_message`。

```python
@bot.command("/help")
def on_help(ctx):
    ctx.reply("📖 帮助信息...")

@bot.command("/status")
def on_status(ctx):
    ctx.reply("✅ 运行正常")

@bot.command("/clear")
def on_clear(ctx):
    # ctx.text 是完整消息，如 "/clear" 或 "/clear all"
    ctx.reply("已清除")
```

!!! note "路由优先级"
    1. `@bot.command` 最优先（精确匹配指令前缀）
    2. `@bot.regex` 次之（按注册顺序，第一个匹配即停止）
    3. `@bot.on_message` 兜底（按注册顺序，第一个匹配即停止）

### @bot.regex — 正则匹配

```python
@bot.regex(r"^查询\s+(.+)$")
def on_query(ctx):
    keyword = ctx._match.group(1)  # 正则捕获组
    ctx.reply(f"🔍 正在查询：{keyword}")

@bot.regex(r"^天气\s*(\S+)?")
def on_weather(ctx):
    city = ctx._match.group(1) or "北京"
    ctx.reply(f"🌤 {city}今日晴，22°C")
```

---

## 处理不同消息类型

```python
@bot.on_message
def handle(ctx):
    if ctx.msg_type == "text":
        ctx.reply(f"文字消息：{ctx.text}")

    elif ctx.msg_type == "image":
        content = ctx.get_content()
        image_key = content.get("image_key")
        ctx.reply(f"收到图片，key={image_key}")

    elif ctx.msg_type == "file":
        content = ctx.get_content()
        ctx.reply(f"收到文件，key={content.get('file_key')}")

    elif ctx.msg_type == "post":
        ctx.reply("收到富文本消息")

    else:
        ctx.reply(f"收到 {ctx.msg_type} 类型消息")
```

---

## 机器人进群事件

```python
@bot.on_bot_added
def welcome(chat_id):
    """机器人被拉入群时自动发欢迎消息"""
    bot.send_text(chat_id, "chat_id",
        "大家好！我是 AI 助手 🤖\n"
        "发送 /help 查看可用指令。"
    )
```

---

## 多处理器注册示例

```python
bot = LarkBot()

# 指令（最高优先级）
@bot.command("/help")
def help_cmd(ctx): ...

@bot.command("/clear")
def clear_cmd(ctx): ...

# 正则（次优先级）
@bot.regex(r"^查询\s+(.+)$")
def query_handler(ctx): ...

# 群聊特定处理
@bot.on_message(group_only=True)
def group_handler(ctx):
    # 只有在群聊中才触发
    ...

# 最终兜底
@bot.on_message
def fallback(ctx):
    ctx.reply("不明白，发送 /help 查看帮助")

# 机器人进群
@bot.on_bot_added
def welcome(chat_id): ...

bot.start()
```

---

## 错误处理

处理函数中的异常会被自动捕获并记录日志，不会导致机器人崩溃：

```python
@bot.on_message
def risky_handler(ctx):
    try:
        result = some_api_call()
        ctx.reply(result)
    except Exception as e:
        ctx.reply(f"⚠️ 处理出错：{e}")
```

---

## 所需权限

| 操作 | 权限 |
|------|------|
| 接收私聊消息 | `im:message.receive_v1`（事件权限） |
| 接收群聊消息 | `im:message.receive_v1`（事件权限） |
| 发送回复 | `im:message` |
| 获取发送者详细信息 | `contact:user.base:readonly` |
