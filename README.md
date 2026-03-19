<div align="center">
    <a href="https://pypi.python.org/pypi/chattool">
        <img src="https://img.shields.io/pypi/v/chattool.svg" alt="PyPI version" />
    </a>
    <a href="https://github.com/cubenlp/chattool/actions/workflows/ci.yml">
        <img src="https://github.com/cubenlp/chattool/actions/workflows/ci.yml/badge.svg" alt="Tests" />
    </a>
    <a href="https://chattool.wzhecnu.cn">
        <img src="https://img.shields.io/badge/docs-github_pages-blue.svg" alt="Documentation Status" />
    </a>
    <a href="https://codecov.io/gh/cubenlp/chattool">
        <img src="https://codecov.io/gh/cubenlp/chattool/branch/master/graph/badge.svg" alt="Coverage" />
    </a>
</div>

<div align="center">
    <img src="https://qiniu.wzhecnu.cn/PicBed6/picgo/chattool.jpeg" alt="ChatAPI Toolkit" width="360" style="border-radius: 20px;">

[English](README_en.md) | [简体中文](README.md)
</div>

以 CLI 为核心的 Python 开发套件，集成 LLM 对话、工具箱（DNS、飞书、绘图等）、MCP 服务和环境管理。

## 安装

```bash
pip install chattool --upgrade
pip install "chattool[images]"   # 含图像工具
pip install "chattool[dev]"      # 含 MCP 等开发依赖
```

## 功能概览

### 环境变量管理 (`chatenv`)

```bash
chatenv init -i                  # 交互式初始化（敏感字段自动隐藏）
chatenv init -i -t openai        # 仅初始化指定服务
chatenv cat                      # 查看配置（敏感值打码）
chatenv set OPENAI_API_KEY=sk-xxx
chatenv save work && chatenv use work   # 多 profile 管理
```

### LLM 对话 (`chattool.Chat`)

```python
from chattool import Chat

# 多轮对话
chat = Chat("Hello!")
chat.get_response()
chat.user("How are you?").get_response()

# 异步并发
import asyncio
base = Chat().system("你是助手")
tasks = [base.copy().user(f"主题 {i}").async_get_response() for i in range(5)]
responses = asyncio.run(asyncio.gather(*tasks))

# 流式输出
async for chunk in Chat().user("写一首诗").async_get_response_stream():
    if chunk.delta_content:
        print(chunk.delta_content, end="", flush=True)
```

### 飞书机器人 (`chattool lark`)

```bash
chattool lark send USER_ID "Hello"
chattool lark send USER_ID --image photo.png
chattool serve lark echo                        # 回显机器人
chattool serve lark ai --system "你是工作助手"  # AI 对话机器人
```

```python
from chattool.tools.lark import LarkBot, ChatSession

bot = LarkBot()
session = ChatSession(system="你是助手")

@bot.on_message
def chat(ctx):
    ctx.reply(session.chat(ctx.sender_id, ctx.text))

bot.start()
```

### DNS 管理 (`chattool dns`)

```bash
chattool dns get home.example.com
chattool dns set home.example.com -v 1.2.3.4
chattool dns ddns home.example.com --monitor
chattool dns cert-update -d example.com -e admin@example.com
```

### AI 绘图 (`chattool image`)

```bash
chattool image pollinations generate "a cat in space" -o cat.png
chattool image siliconflow generate "a cute dog" -o dog.png
```

### 其他工具

| 工具 | 命令 | 说明 |
|------|------|------|
| 网络扫描 | `chattool network` | 扫描局域网主机和端口 |
| MCP 服务 | `chattool mcp start` | 标准 MCP Server，供 Claude/Cursor 调用 |
| 环境安装 | `chattool setup codex/claude` | 安装 Codex / Claude Code 并写入配置 |
| Skills | `chattool skill install` | 安装 ChatTool skills 到 Codex / Claude Code |
| CC-Connect | `chattool cc` | cc-connect 快速配置与启动 |

## 文档

完整文档见 [chattool.wzhecnu.cn](https://chattool.wzhecnu.cn)

## 开源协议

MIT License
