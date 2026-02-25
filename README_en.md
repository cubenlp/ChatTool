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
    <img src="https://qiniu.wzhecnu.cn/PicBed6/picgo/chattool.jpeg" alt="ChatAPI Toolkit" width="360", style="border-radius: 20px;">

[English](README_en.md) | [简体中文](README.md)
</div>


<!-- 
[![Updates](https://pyup.io/repos/github/cubenlp/chattool/shield.svg)](https://pyup.io/repos/github/cubenlp/chattool/) 
-->

A Python toolkit integrating LLM chat, Feishu/Lark bots, DNS management, SSL certificates, and more.

## Installation

```bash
pip install chattool --upgrade
```

## Features

### 1. Environment Management (`chatenv`)

Centralized configuration with automatic secret masking and hidden input for sensitive fields.

```bash
# Interactive init (sensitive fields hidden automatically)
chatenv init -i

# Init only specific service config
chatenv init -i -t openai
chatenv init -i -t feishu

# View config (secrets auto-masked)
chatenv cat

# Filter by type
chatenv cat -t feishu

# Set / get individual values
chatenv set OPENAI_API_KEY=sk-xxx
chatenv get OPENAI_API_KEY

# Profile management
chatenv save work && chatenv use work
```

### 2. Chat (`chattool.Chat`)

OpenAI-compatible chat objects with multi-turn dialogue, batch processing, async concurrency, and streaming.

```python
from chattool import Chat

# Multi-turn dialogue
chat = Chat("Hello!")
resp = chat.get_response()
chat.user("How are you?")
chat.get_response()
chat.save("chat.json", mode="w")

# Async concurrency
import asyncio
base = Chat().system("You are a helpful assistant")
tasks = [base.copy().user(f"Topic {i}").async_get_response() for i in range(5)]
responses = asyncio.run(asyncio.gather(*tasks))

# Streaming
async for chunk in Chat().user("Write a poem").async_get_response_stream():
    if chunk.delta_content:
        print(chunk.delta_content, end="", flush=True)
```

### 3. Feishu/Lark Bot (`chattool lark`)

Send messages, start Echo/AI bots with one command. Supports text, image, file, and rich-text messages.

```bash
# Send messages
chattool lark send -r USER_ID -m "Hello"
chattool lark send -r USER_ID --image photo.png
chattool lark send -r USER_ID --file report.pdf

# Start Echo bot (WebSocket)
chattool serve lark echo

# Start AI conversation bot
chattool serve lark ai --model gpt-4o

# View bot info and permissions
chattool lark info
chattool lark scopes
```

```python
from chattool.tools.lark import LarkBot

bot = LarkBot()
bot.send_text("ou_xxx", "open_id", "Hello!")
bot.send_image_file("ou_xxx", "open_id", "photo.png")

@bot.on_message
def handle(ctx):
    ctx.reply_text(f"Received: {ctx.text}")

bot.start()
```

### 4. DNS Management (`chattool dns`)

Unified DNS interface for Alibaba Cloud and Tencent Cloud, with DDNS and automatic SSL certificate renewal.

```bash
# Query / set DNS records
chattool dns get test.example.com
chattool dns set test.example.com -v 1.2.3.4

# DDNS (public / LAN IP)
chattool dns ddns -d example.com -r home --monitor
chattool dns ddns -d example.com -r nas --ip-type local --local-ip-cidr 192.168.1.0/24

# SSL certificate auto-renewal
chattool dns cert-update -d example.com -e admin@example.com --cert-dir ./certs
```

### 5. Other Tools

| Tool | Command | Description |
|------|---------|-------------|
| Network Scan | `chattool network scan` | Scan LAN for active hosts and SSH ports |
| MCP Server | `chattool mcp inspect` | Inspect MCP server capabilities |
| Screenshot | `chattool serve capture` | Local webpage screenshot service |
| Cert Mgmt | `chattool serve cert` / `chattool client cert` | SSL certificate distribution |

## License

MIT License. See the LICENSE file for details.

## Changelog

- `5.3.0` — Feishu/Lark bot (messaging, event routing, AI chat), CLI tools (`chattool lark`, `chattool serve lark`)
- `5.0.0` — DNS management (Aliyun/Tencent), DDNS, SSL cert auto-renewal, centralized env config
- `4.1.0` — Unified `Chat` API (sync/async/stream), env-based configuration
- For earlier changes, please refer to the repository commits.