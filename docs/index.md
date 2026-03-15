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

ChatTool 是一个以 CLI 为核心的 Python 开发套件，集成 LLM 对话、工具箱（DNS、飞书、绘图等）、MCP 服务和环境管理。

## 架构概览

```mermaid
graph TB
    subgraph 基础设施
        direction LR
        CFG[⚙️ config\n环境变量]
        SETUP[🔧 setup / docker\n环境构建]
    end

    subgraph 核心能力
        direction LR
        LLM[🤖 llm\nLLM 对话]
        TOOLS[🧰 tools\nDNS · 飞书 · 绘图 · 网络]
    end

    subgraph 接入形式
        direction LR
        CLIENT[💻 client\n本地 CLI]
        SERVE[☁️ serve\n远程服务]
        MCP[🔌 mcp\nAI 协议]
    end

    SKILLS[✨ skills — 能力出口]

    基础设施 --> 核心能力
    核心能力 --> 接入形式
    接入形式 --> SKILLS
```

**开发逻辑**

ChatTool 按层构建：

- `config` 和 `setup/docker` 是基础设施——前者管理所有模块的环境变量和凭证，后者负责运行环境的构建（Chrome、FRP、Nginx 等）。
- `llm` 和 `tools` 是核心能力层，两者并行发展。`llm` 提供 LLM 路由和对话接口，`tools` 实现各类具体功能（DNS、飞书、绘图等），每个 tool 内部提供 Python API、CLI 和 MCP 三种接入形式。
- `client/serve/mcp` 是封装加工层——`client` 把能力暴露为本地 CLI，`serve` 把敏感或重计算的操作拆到云端，`mcp` 实现标准 MCP Server 供 Claude/Cursor 等 AI 客户端直接调用。
- `skills` 是能力出口，把以上所有封装好的功能收敛为可复用的 skill 片段，注入 Codex/Claude Code，让 AI agent 能直接调用 ChatTool 的能力。

## 安装

```bash
pip install chattool --upgrade

# 含图像工具
pip install "chattool[images]"

# 含开发依赖（MCP 等）
pip install "chattool[dev]"
```

## 快速上手

### 环境变量

```bash
chatenv init -i          # 交互式初始化
chatenv cat              # 查看当前配置（敏感值打码）
chatenv set OPENAI_API_KEY=sk-xxx
```

### LLM 对话

```python
from chattool import Chat

chat = Chat("你好")
resp = chat.get_response()
print(resp.content)
```

### 飞书机器人

```bash
chattool lark send USER_ID "Hello"
chattool serve lark ai --system "你是工作助手"
```

### DNS 管理

```bash
chattool dns get home.example.com
chattool dns ddns home.example.com --monitor
```

## 板块说明

| 层次 | 板块 | 说明 |
|------|------|------|
| 基础设施 | `config` | 环境变量管理，所有模块的配置来源 |
| 基础设施 | `setup / docker` | 环境构建脚本，为 tools 提供运行环境 |
| 核心能力 | `llm` | LLM 路由、对话对象、异步并发 |
| 核心能力 | `tools` | DNS、飞书、绘图、网络扫描等具体工具 |
| 封装加工 | `client` | 本地 CLI，直接调用 llm/tools |
| 封装加工 | `serve` | 远程服务，解耦算力和密钥敏感操作 |
| 封装加工 | `mcp` | MCP Server，供 Claude/Cursor 等 AI 客户端调用 |
| 能力出口 | `skills` | 把上层能力收敛为可复用的 skill，注入 Codex/Claude Code |

## 开发规范

### CLI 交互原则

- 必要参数缺失时自动触发 interactive 模式
- `-i` 强制开启交互，`-I` 强制关闭（参数不全则报错）
- 参数默认值从环境变量读取，敏感值在提示中自动 mask

### 代码规范

- **最小 import**：把 import 放到函数内部，避免 CLI 启动变慢
- **工具结构**：每个工具放 `tools/<name>/`，提供 `cli.py`、`mcp.py`（如有）
- **新增 CLI**：同步更新 `docs/` 对应文档和 `AGENTS.md`

### 分支与发布

- 功能分支：`rex/<feature>`
- 主分支：`master`
- 版本号遵循 [Semantic Versioning](https://semver.org/)
