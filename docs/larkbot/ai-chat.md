# AI 对话集成

`ChatSession` 是将飞书机器人与 LLM 集成的核心组件。它为每个用户维护独立的对话历史，并通过 `chattool.Chat` 调用大语言模型。

---

## 前置条件

除了飞书凭证，还需要配置 LLM 访问凭证：

```bash title=".env"
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx

# OpenAI（或兼容接口）
OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=https://api.openai.com/v1  # 可选，默认值
```

---

## 快速开始

```python
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

---

## ChatSession API

### 创建会话管理器

```python
session = ChatSession(
    system="你是一个工作助手",  # System Prompt，所有用户共享
    max_history=10,            # 最多保留最近 10 轮对话（None=不限制）
)
```

### chat() — 发起对话

```python
reply = session.chat(user_id, text)
# user_id: 用户标识符（通常用 ctx.sender_id）
# text:    用户的消息文字
# 返回:    LLM 生成的回复字符串
```

每次调用 `chat()` 会：

1. 为该 `user_id` 创建或复用一个 `Chat` 实例
2. 调用 `Chat.ask(text)`（= 添加用户消息 + 请求 API + 返回回复）
3. 会话历史自动保留在 `Chat` 实例中

### clear() / clear_all() — 清除历史

```python
session.clear("rexwzh")   # 清除单个用户的对话历史
session.clear_all()        # 清空所有用户的会话
```

### 查询状态

```python
session.has_session("rexwzh")  # 是否已有会话 → bool
session.user_count()            # 当前活跃会话数 → int
```

---

## 多用户隔离

每个 `user_id` 对应完全独立的 `Chat` 实例，历史记录互不干扰：

```python
session = ChatSession(system="你是助手")

# Alice 和 Bob 独立对话
session.chat("alice", "我叫 Alice，我喜欢 Python")
session.chat("bob",   "我叫 Bob，我喜欢 Go")

# Alice 询问，只能看到自己的历史
reply = session.chat("alice", "你还记得我叫什么名字吗？")
# LLM 回复：记得，你叫 Alice（因为 Alice 的历史中有这句话）
```

---

## 限制对话轮数

长对话会导致 token 消耗过多。使用 `max_history` 限制保留的轮数：

```python
session = ChatSession(
    system="你是助手",
    max_history=5  # 只保留最近 5 轮
)
```

每轮 = 1条用户消息 + 1条助手回复。  
System Prompt 始终保留，不计入 `max_history`。

---

## 指令设计建议

```python
session = ChatSession(system="你是工作助手")

@bot.command("/clear")
def on_clear(ctx):
    """清除当前用户的对话历史"""
    session.clear(ctx.sender_id)
    ctx.reply("✅ 记忆已清除，我们重新开始！")

@bot.command("/help")
def on_help(ctx):
    ctx.reply(
        "🤖 AI 助手指令：\n"
        "  /help   — 显示帮助\n"
        "  /clear  — 清除对话记忆\n"
        "  /status — 查看运行状态\n\n"
        "直接发消息即可开始对话！"
    )

@bot.command("/status")
def on_status(ctx):
    total = session.user_count()
    has = session.has_session(ctx.sender_id)
    ctx.reply(
        f"📊 运行状态\n"
        f"  活跃会话：{total} 个\n"
        f"  你的会话：{'已建立' if has else '未开始'}"
    )

@bot.on_message
def on_chat(ctx):
    if not ctx.text.strip():
        return
    try:
        reply = session.chat(ctx.sender_id, ctx.text)
        ctx.reply(reply)
    except Exception as e:
        ctx.reply(f"⚠️ AI 服务暂时不可用：{e}")
```

---

## 自定义 System Prompt 场景

通过更换 `system` 快速适配不同场景：

=== "代码助手"

    ```python
    session = ChatSession(
        system="你是一个 Python 编程助手。"
               "指出代码中的问题并给出改进建议，代码示例要简洁。"
    )
    ```

=== "HR 问答"

    ```python
    session = ChatSession(
        system="你是公司 HR 助手，负责回答员工关于假期、薪资、福利的问题。"
               "友好专业，如果不确定请建议联系 HR 部门。"
    )
    ```

=== "文档问答"

    ```python
    doc_context = open("product_docs.txt").read()
    
    session = ChatSession(
        system=f"你是产品文档助手，基于以下文档回答问题，不要编造：\n\n{doc_context}"
    )
    ```

=== "多语言支持"

    ```python
    session = ChatSession(
        system="你是一个多语言助手。"
               "检测用户消息的语言，用相同语言回复。"
    )
    ```

---

## 使用自定义 Chat 工厂

如果需要自定义 `Chat` 实例的初始化（如设置特定模型、temperature 等）：

```python
from chattool import Chat

def my_factory():
    chat = Chat()
    chat.system("你是专业的技术支持工程师")
    # 可以在这里设置模型参数等
    return chat

session = ChatSession(chat_factory=my_factory)
```

---

## 注意事项

!!! warning "并发安全"
    `ChatSession` 使用内存字典存储会话，在多进程或多机部署时，各实例之间的会话**不共享**。  
    如果需要跨进程共享会话，请自行实现基于 Redis 的工厂函数。

!!! tip "token 成本控制"
    - 设置合理的 `max_history`（推荐 5-10 轮）
    - System Prompt 不要过长
    - 对高频问题考虑缓存或规则匹配，减少 LLM 调用

!!! note "空消息处理"
    当用户发送图片、文件等非文本消息时，`ctx.text` 为空串。  
    建议在调用 `session.chat()` 前检查：
    ```python
    if not ctx.text.strip():
        ctx.reply("暂不支持该消息类型")
        return
    ```
