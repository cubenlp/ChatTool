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
pip install "chattool[setup]"  # installs ChatUp; use chatup workspace/hermes/cc-connect
```

Minimum supported Python version: `3.10`.

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

### 4. DNS Management (moved to ChatDNS)

DNS record management, DDNS, and IP detection now live in the standalone `ChatDNS` package. Use the first-level `chatdns` CLI:

```bash
chatdns --help
chatdns records test.example.com
chatdns set test.example.com -v 1.2.3.4
chatdns ddns -d example.com -r home --monitor
chatdns ddns -d example.com -r nas --ip-type local --local-ip-cidr 192.168.1.0/24
```

Install through ChatTool's optional dependency with `pip install "chattool[dns]"`. The nested `chattool dns` command has been removed so ChatTool no longer carries duplicate DNS implementation.

### 5. AI Image Generation (`chattool image`)

Supports Tongyi, Hugging Face, LiblibAI, Pollinations.ai, and SiliconFlow.

```bash
# Install image dependencies
pip install "chattool[images]"

# Pollinations (requires POLLINATIONS_API_KEY)
chattool image pollinations list-models
chattool image pollinations generate "a cat in space" -o cat.png

# SiliconFlow (requires SILICONFLOW_API_KEY)
chattool image siliconflow list-models
chattool image siliconflow generate "a cute dog" -o dog.png
```

### 6. Nginx Config Generation (`chattool nginx`)

```bash
chattool nginx --list
chattool nginx proxy-pass --set SERVER_NAME=app.example.com --set PROXY_PASS=http://127.0.0.1:8080
chattool nginx websocket-proxy ./websocket.conf --set SERVER_NAME=ws.example.com --set PROXY_PASS=http://127.0.0.1:3000
chattool nginx -i
```

### 7. Local Services (`chattool serve`)

```bash
chattool serve local ./cli-tree.html --host 127.0.0.1 --port 8765
chattool serve local ./reports --html cli-tree.html --port 8765
chattool serve local . --html index.html --dry-run
```

`serve local` opens a local HTML file or directory through a configurable local port. If `TARGET` is omitted, it defaults to the current directory; `-i` uses the shared interactive prompt flow.

### 8. Other Tools

| Tool | Command | Description |
|------|---------|-------------|
| Network Scan | `chattool network scan` | Scan LAN for active hosts and SSH ports |
| Nginx Config | `chattool nginx` | Generate template-based reverse proxy and static site configs |
| MCP Server | `chattool mcp info` / `chattool mcp inspect` | Inspect MCP server capabilities (JSON supported) |
| Screenshot | `chattool serve capture` | Local webpage screenshot service |
| Local HTML | `chattool serve local` | Serve a local HTML file or directory |
| Cert Mgmt | `chattool serve cert` / `chattool client cert` | SSL certificate distribution |
| Setup | `chatup codex/claude/opencode/hermes` | ChatTool setup has moved to the standalone ChatUp package. Install `chattool[setup]` or `chatup`, then use first-level `chatup ...` commands. |
| Workspace | `chatup workspace` | Create a collaboration workspace around a core project with `projects/` as the execution container and workspace-level files as the general-use protocol layer; supports `--with-chattool`, `--with-chatblog`, and `--with-memory` |
| Skills | `chattool skill install` | Install ChatTool skills to Codex / Claude / OpenCode |
| CC-Connect | `chattool cc` | Quick cc-connect setup and start |

## Environment Profiles

Since ChatTool 7.0.0, typed env profiles live under `~/.chatarch/envs` by default. Set `CHATARCH_HOME` to redirect the ChatArch root. The old `~/.config/chattool/envs` path is no longer read as a fallback.

To manually copy legacy profiles into the new root from a repository checkout:

```bash
python scripts/migrate_chattool_envs_to_chatarch.py --dry-run
python scripts/migrate_chattool_envs_to_chatarch.py
```

## PyPI Package Scaffolding

```bash
chattool pypi init mychat
chattool pypi init mycli -t chatarch
chattool pypi init -i                  # Interactive template, mkdocs, and workflow options
chattool pypi probe mychat
chatpypi mychat
```

The default template writes `requires-python = ">=3.9"`. The `chatarch` template writes `requires-python = ">=3.10"`, depends on `chatstyle>=0.1.0` and `chatenv>=0.1.1`, and adds `README.en.md`, `mkdocs.yml`, docs, tests, and GitHub workflows. Its publish workflow is triggered by explicit `v*` tags or `workflow_dispatch`, checks that the tag matches package `__version__`, and publishes missing versions through PyPI Trusted Publishing with `environment: pypi` instead of repository-level PyPI token secrets. Use `--without-mkdocs` or `--without-workflows` to skip those optional files.

`chattool pypi probe <name>` checks the exact project name on PyPI by default and prints a concise blocking result plus useful package metadata, including the latest release date, when the name already exists.

## License

MIT License. See the LICENSE file for details.

## Changelog

- `5.3.0` — Feishu/Lark bot (messaging, event routing, AI chat), CLI tools (`chattool lark`, `chattool serve lark`)
- `5.0.0` — DNS management (Aliyun/Tencent), DDNS, SSL cert auto-renewal, centralized env config
- `4.1.0` — Unified `Chat` API (sync/async/stream), env-based configuration
- For earlier changes, please refer to the repository commits.
