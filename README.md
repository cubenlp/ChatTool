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

集成 LLM 对话、飞书机器人、DNS 管理、SSL 证书等工具的 Python 开发套件。

## 安装

```bash
pip install chattool --upgrade
```

## 功能概览

### 1. 环境变量管理 (`chatenv`)

集中式配置管理，密码类字段自动脱敏显示，交互模式隐藏敏感输入。

```bash
# 交互式初始化（敏感字段自动隐藏输入）
chatenv init -i

# 仅初始化指定服务配置
chatenv init -i -t openai
chatenv init -i -t feishu

# 查看全部配置（敏感值自动打码）
chatenv cat

# 按类型过滤查看
chatenv cat -t feishu

# 设置 / 查看单项
chatenv set OPENAI_API_KEY=sk-xxx
chatenv get OPENAI_API_KEY

# 多配置 profile 管理
chatenv save work && chatenv use work
```

### 2. Chat 对话 (`chattool.Chat`)

基于 OpenAI API 的对话对象，支持多轮对话、批量处理、异步并发和流式输出。

```python
from chattool import Chat

# 多轮对话
chat = Chat("Hello!")
resp = chat.get_response()
chat.user("How are you?")
chat.get_response()
chat.save("chat.json", mode="w")

# 异步并发
import asyncio
base = Chat().system("你是一个有用的助手")
tasks = [base.copy().user(f"主题 {i}").async_get_response() for i in range(5)]
responses = asyncio.run(asyncio.gather(*tasks))

# 流式输出
async for chunk in Chat().user("写一首诗").async_get_response_stream():
    if chunk.delta_content:
        print(chunk.delta_content, end="", flush=True)
```

### 3. 飞书/Lark 机器人 (`chattool lark`)

一行命令发消息、启动 Echo/AI 机器人，支持文本、图片、文件、富文本等消息类型。

```bash
# 发送消息
chattool lark send -r USER_ID -m "Hello"
chattool lark send -r USER_ID --image photo.png
chattool lark send -r USER_ID --file report.pdf

# 启动 Echo 机器人（WebSocket）
chattool serve lark echo

# 启动 AI 对话机器人
chattool serve lark ai --model gpt-4o

# 查看机器人信息和权限
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
    ctx.reply_text(f"收到: {ctx.text}")

bot.start()
```

### 4. DNS 管理 (`chattool dns`)

统一的 DNS 接口，支持阿里云和腾讯云，提供 DDNS 动态更新和 SSL 证书自动续期。

```bash
# 查询 / 设置 DNS 记录
chattool dns get test.example.com
chattool dns set test.example.com -v 1.2.3.4

# DDNS 动态域名 (公网 / 局域网)
chattool dns ddns -d example.com -r home --monitor
chattool dns ddns -d example.com -r nas --ip-type local --local-ip-cidr 192.168.1.0/24

# SSL 证书自动更新
chattool dns cert-update -d example.com -e admin@example.com --cert-dir ./certs
```

### 5. 其他工具

| 工具 | 命令 | 说明 |
|------|------|------|
| 网络扫描 | `chattool network scan` | 扫描局域网活跃主机和 SSH 端口 |
| MCP 服务 | `chattool mcp inspect` | MCP Server 能力检查 |
| 截图服务 | `chattool serve capture` | 本地网页截图服务 |
| 证书分发 | `chattool serve cert` / `chattool client cert` | SSL 证书集中管理与客户端拉取 |

## 开源协议

MIT License

## 更新日志

- `5.3.0` — 飞书机器人（消息收发、事件路由、AI 对话）、CLI 工具链（`chattool lark`、`chattool serve lark`）
- `5.0.0` — DNS 管理（阿里云/腾讯云）、DDNS、SSL 证书自动续期、环境变量集中管理
- `4.1.0` — 统一 `Chat` API（同步/异步/流式），默认环境变量配置
- 更早版本请参考仓库提交记录