# chattool setup hermes

`chattool setup hermes` 用于安装 Hermes Agent，可选准备或启动 Hermes WebUI，并把 ChatTool typed env 中已有的 OpenAI / Feishu 配置写入 Hermes。

## 安装内容

默认安装目标：

- Agent 源码：如果当前目录已有 `./hermes`，则使用 `./hermes`；否则使用 `~/.hermes/hermes-agent`。
- WebUI 源码：如果当前目录已有 `./hermes-webui`，则使用 `./hermes-webui`；否则使用 `~/.hermes/hermes-webui`。
- Python 运行环境：Hermes Agent 源码目录下的 `venv`。
- CLI 入口：`~/.local/bin/hermes`，指向 `<agent-dir>/venv/bin/hermes`。
- 状态与密钥目录：`~/.hermes/`。

默认安装的是轻量 Hermes extras：

```text
messaging,cli,pty,cron,feishu,web,acp,mcp
```

这样可以避开官方 `.[all]` 路径中的可选 RL、voice、browser 等重依赖；这些能力不是基础 Agent + WebUI + Feishu 配置的必要条件。

## 配置来源

OpenAI-compatible 模型配置按以下优先级解析：

1. 显式 CLI 参数：`--api-key`、`--base-url`、`--model`。
2. `-e/--env`：OpenAI `.env` 文件路径，或已保存的 OpenAI profile 名称。
3. 当前 shell 环境变量。
4. ChatTool 当前激活的 OpenAI typed env。
5. 默认值：`https://api.openai.com/v1`、`gpt-5.4-mini`。

Feishu 配置按以下优先级解析：

1. `--feishu-env`：Feishu `.env` 文件路径，或已保存的 Feishu profile 名称。
2. 当前 shell 环境变量。
3. ChatTool 当前激活的 Feishu typed env。

命令会写入：

- `~/.hermes/.env`：密钥、OpenAI-compatible endpoint、Feishu gateway 环境变量。
- `~/.hermes/config.yaml`：默认模型、provider、terminal 等 Hermes 配置。
- `<webui-dir>/.env`：WebUI 自动发现 Agent、Python、状态目录和本地端口所需配置。

密钥只写入本机文件，不应提交到 Git 仓库。

## 使用方式

只预览计划，不写文件、不执行安装：

```bash
chattool setup hermes --dry-run -I
```

在当前 research project 内安装，并复用 ChatTool 当前激活的 typed env：

```bash
chattool setup hermes --agent-dir ./hermes --webui-dir ./hermes-webui
```

显式指定 OpenAI / Feishu profile：

```bash
chattool setup hermes -e apple --feishu-env rexwzh
```

安装并启动 WebUI：

```bash
chattool setup hermes --agent-dir ./hermes --webui-dir ./hermes-webui --start-webui
```

只安装依赖和 CLI 链接，不写模型或 Feishu 配置：

```bash
chattool setup hermes --install-only
```

## WebUI 与 Agent 的绑定关系

一个 Hermes WebUI server 进程启动时绑定一套 Hermes Agent runtime，主要由这些变量决定：

- `HERMES_WEBUI_AGENT_DIR`
- `HERMES_WEBUI_PYTHON`
- `HERMES_HOME`
- `HERMES_CONFIG_PATH`

因此默认模型是“一套 WebUI 绑定一套 Hermes Agent runtime”。同一个 WebUI 内仍然可以有多个 sessions、workspaces 和 profiles。如果需要多套相互隔离的 Hermes 后端，可以启动多个 WebUI 进程，并为每个进程设置不同的端口、`HERMES_HOME` 和 `HERMES_WEBUI_AGENT_DIR`。

## 验证命令

安装后建议执行：

```bash
hermes version
hermes status
hermes doctor
hermes -z 'Reply with exactly: HERMES_OK' --ignore-rules
curl --noproxy '*' http://127.0.0.1:8787/health
```

如果本机配置了 HTTP 代理，本地 WebUI 健康检查建议使用 `--noproxy '*'`，或设置：

```bash
export NO_PROXY=127.0.0.1,localhost
export no_proxy=127.0.0.1,localhost
```
