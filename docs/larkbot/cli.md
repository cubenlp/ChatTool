# 命令行工具

`chattool` 提供一组 CLI 命令，无需编写 Python 代码即可完成常见的飞书机器人操作。

## 命令总览

```
chattool lark          # 飞书客户端工具
├── info               # 查看机器人信息（验证凭证）
├── send               # 发送消息
├── reply              # 引用回复消息
├── listen             # WebSocket 监听调试
└── chat               # 终端 AI 对话

chattool serve lark    # 飞书机器人服务
├── echo               # 回显机器人
├── ai                 # AI 对话机器人
└── webhook            # 空 Webhook（平台验证）
```

## 前置条件

1. 安装 `chattool[tools]`
2. 设置环境变量（或 `.env` 文件）：

```bash
export FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
export FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## chattool lark

### info — 验证凭证

```bash
chattool lark info
```

输出机器人名称、Open ID 和激活状态，可用于快速验证 App ID / Secret 是否正确。

### send — 发送消息

```bash
# 发送文本
chattool lark send rexwzh "你好，世界"

# 指定 ID 类型（默认 user_id）
chattool lark send oc_xxxxx "群通知" -t chat_id

# 发送卡片消息（JSON 文件）
chattool lark send rexwzh "" --card card.json

# 发送富文本消息（JSON 文件）
chattool lark send rexwzh "" --post post.json
```

| 参数 | 说明 |
|------|------|
| `RECEIVER` | 接收者 ID |
| `TEXT` | 消息文本（使用 `--card` 或 `--post` 时被忽略） |
| `-t, --type` | ID 类型：`open_id` / `user_id` / `union_id` / `email` / `chat_id` |
| `-c, --card` | 卡片 JSON 文件路径 |
| `-p, --post` | 富文本 JSON 文件路径 |

### reply — 引用回复

```bash
chattool lark reply om_xxxxxx "收到，已处理"
```

### listen — WebSocket 调试

实时打印收到的消息，适合调试事件订阅：

```bash
chattool lark listen
chattool lark listen -v  # 打印完整 JSON
```

!!! note "前提"
    需在飞书平台「事件订阅」中选择长连接模式，并订阅 `im.message.receive_v1`。

### chat — 终端 AI 对话

不经过飞书，直接在终端与 LLM 对话，适合调试 System Prompt：

```bash
chattool lark chat
chattool lark chat --system "你是一名翻译官，将用户输入翻译为英文"
chattool lark chat --max-history 5
```

内置命令：`/clear` 清除历史、`/quit` 退出。

!!! note "依赖"
    终端 AI 对话需要配置 `OPENAI_API_KEY`（或 `chattool` 支持的其他 LLM 凭证）。

---

## chattool serve lark

启动一个完整的飞书机器人服务，支持 WebSocket 和 Flask Webhook 两种模式。

### echo — 回显机器人

收到什么就回复什么，用于验证收发链路：

```bash
chattool serve lark echo                     # WebSocket 模式（默认）
chattool serve lark echo --mode flask -p 8080  # Flask Webhook 模式
```

### ai — AI 对话机器人

一行命令启动带多轮记忆的 AI 机器人：

```bash
chattool serve lark ai
chattool serve lark ai --system "你是一名翻译官" --max-history 20
chattool serve lark ai --mode flask --port 8080
```

| 参数 | 说明 |
|------|------|
| `-m, --mode` | `ws`（WebSocket，默认）或 `flask`（Webhook） |
| `-s, --system` | System Prompt |
| `-n, --max-history` | 每用户最多保留的对话轮数 |
| `--model` | LLM 模型名称（留空使用默认） |
| `--host` | Flask 监听地址（仅 flask 模式） |
| `-p, --port` | Flask 监听端口（仅 flask 模式） |

内置 `/clear` 和 `/help` 指令。

### webhook — 平台验证服务

启动空的 Webhook 服务，仅用于飞书平台 URL 验证（challenge 验证）：

```bash
chattool serve lark webhook
chattool serve lark webhook --port 8080 --path /lark/events
```

验证通过后，可以改用 `echo` 或 `ai` 子命令来启动实际业务逻辑。

---

## 典型工作流

```bash
# 1. 验证凭证
chattool lark info

# 2. 发送测试消息
chattool lark send rexwzh "CLI 测试消息"

# 3. 调试事件接收
chattool lark listen -v

# 4. 启动 AI 机器人
chattool serve lark ai --system "你是一个飞书工作助手"
```
