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

支持 Python `>=3.9`。

## 安装

默认安装只包含核心聊天能力和基础 CLI。DNS、MCP、Serve、交互式 TUI 等较重依赖已拆到 extras。

```bash
pip install chattool --upgrade
pip install "chattool[tools]"        # 常用工具全集
pip install "chattool[mcp,dns]"      # MCP 服务 + DNS 工具
pip install "chattool[images]"       # 含图像工具
pip install "chattool[pypi]"         # 含 Python 包构建/发布依赖
pip install "chattool[dev]"          # 仓库开发依赖
```

## 功能概览

### 环境变量管理 (`chatenv`)

```bash
chatenv init -i                  # 交互式初始化（敏感字段自动隐藏）
chatenv init -i -t openai        # 仅初始化指定服务
chatenv cat                      # 查看配置（敏感值打码）
chatenv cat -t feishu           # 查看飞书配置，供 chattool cc init 默认候选值参考
chatenv set OPENAI_API_KEY=sk-xxx
chatenv new mini -t feishu      # 从当前激活配置复制一份新的 Feishu profile
chatenv new -t openai           # 交互式创建 OpenAI profile：先问名称，再补齐字段，不改 active .env
chatenv save work -t openai && chatenv use work -t openai   # 按类型管理 profile
chattool lark info -e work       # 显式使用 Feishu profile，优先级高于当前 shell 环境变量
chattool cc init -i --quiet      # 生成默认 quiet 的 cc-connect 项目配置
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
chattool lark send "Hello"                  # 使用 FEISHU_DEFAULT_RECEIVER_ID
chattool lark send -t chat_id "Hello team" # 使用 FEISHU_DEFAULT_CHAT_ID
chattool lark info
chattool setup lark-cli
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
chattool dns
chattool dns get home.example.com
chattool dns set home.example.com -v 1.2.3.4
chattool dns ddns home.example.com --monitor
chattool dns cert-update -d example.com -e admin@example.com
```

交互终端里直接运行 `chattool dns` 会先进入命令选择；`get` / `set` / `ddns` 缺少必要参数时会自动补问，`-I` 才会禁用交互并直接报错。

### Nginx 配置生成 (`chattool nginx`)

```bash
chattool nginx --list
chattool nginx proxy-pass --set SERVER_NAME=app.example.com --set PROXY_PASS=http://127.0.0.1:8080
chattool nginx websocket-proxy ./websocket.conf --set SERVER_NAME=ws.example.com --set PROXY_PASS=http://127.0.0.1:3000
chattool nginx static-root ./nas.conf --set SERVER_NAME=share.example.com --set ROOT_DIR=/storage/nas
chattool nginx -i  # 交互式选择模板并逐项填写
```

### AI 绘图 (`chattool image`)

```bash
chattool image pollinations generate "a cat in space" -o cat.png
chattool image siliconflow generate "a cute dog" -o dog.png
```

### 数据探索 (`chattool explore`)

```bash
chattool explore arxiv search -p ai4math -n 10
chattool explore arxiv daily -p math-formalization --days 3
chattool explore arxiv daily -p math-formalization-weekly --days 7 -v
chattool explore arxiv get 1706.03762 -v
```

### 其他工具

| 工具 | 命令 | 说明 |
|------|------|------|
| 网络扫描 | `chattool network` | 扫描局域网主机和端口 |
| Nginx 配置 | `chattool nginx` | 按模板生成常见的反向代理、路径转发和静态目录配置 |
| PyPI 工具 | `chattool pypi` | 创建、构建、校验、上传与探测 Python 包 |
| MCP 服务 | `chattool mcp start` | 标准 MCP Server，供 Claude/Cursor 调用 |
| 环境安装 | `chattool setup codex/claude/opencode/lark-cli/docker` | 安装或检查常用 CLI / Docker 环境，并在确认后执行建议的系统命令 |
| Playground | `chattool setup playground` | 初始化带 `ChatTool/` 仓库的协作工作区，默认生成中文外层模板，外层结构对齐 `reports/`、`playgrounds/`、`knowledge/`，支持 `--language en`，并可复用 GitHub token 配置 Git HTTPS 鉴权 |
| Workspace | `chattool setup workspace` | 初始化围绕核心项目的人类-AI 协作工作区骨架，默认采用 `reports/` 和 `playgrounds/` 的多任务并发结构 |
| Skills | `chattool skill install` | 安装 ChatTool skills 到 Codex / Claude / OpenCode |
| CC-Connect | `chattool cc` | cc-connect 快速配置与启动 |

## 文档

完整文档见 [chattool.wzhecnu.cn](https://chattool.wzhecnu.cn)
仓库结构设计草案见 `docs/design/python-library-repo-structure.md`
PyPI 发布命令设计草案见 `docs/design/chattool-pypi-cli-design.md`

## 测试约定

- `cli-tests/`：真实 CLI 链路与真实环境验收，采用 doc-first。
- `mock-cli-tests/`：所有基于 `mock`、`patch`、`monkeypatch`、fake client / API 的 CLI 测试，统一集中到这里。
- 仓库根下 `tests/` 仅保留历史参考，不再作为新的 CLI 测试主落点。

快速建包可直接运行：

```bash
chattool pypi init mychat
chattool pypi init cli-style mycli
```

默认生成的 `pyproject.toml` 会写入 `requires-python = ">=3.9"`。

`cli-style` 模板会额外生成 `DEVELOP.md`、`setup.md`、`CHANGELOG.md`、`AGENTS.md`、`docs/`、`cli-tests/`、`mock-cli-tests/` 与 `.github/workflows/` 骨架，并默认依赖 `chatstyle` 作为可复用 CLI 运行时。

`chattool pypi` 现在只保留最小命令集：`init/build/check/upload/probe`。其中 `upload` 只是对原始 `twine upload` 的薄封装，不再接管凭证、仓库和交互逻辑。

其中 `chattool pypi probe` 现在默认面向正式 `pypi`，按精确项目名检查名称是否已被占用；若命中现有项目，会顺手输出少量项目摘要信息，便于快速判断是否需要换名。

## 开源协议

MIT License
