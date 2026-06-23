# chattool setup hermes

`chattool setup hermes` 用于封装 ChatArch 维护的 Hermes `install.sh`，并在安装后做少量基础配置。它不是 Hermes 的第二套安装器：默认安装 ChatArch 当前 Hermes 最新版，不安装 WebUI，不自动导入 Feishu，也不默认启动 WebUI。

## Installer 来源

默认 installer 解析顺序：

1. `--installer /path/to/install.sh`
2. `~/.cache/chattool/hermes/install.sh`
3. ChatTool 随包资源 `chattool/setup/assets/hermes/install.sh`

只有显式传入 `--update-installer` 时，才从 ChatArch Hermes URL 下载并更新缓存：

```text
https://raw.githubusercontent.com/ChatArch/hermes-agent/main/scripts/install.sh
```

命令会输出 installer path 和 sha256，便于确认实际使用的脚本。

## 基础用法

```bash
chattool setup hermes
chattool setup hermes --update-installer
chattool setup hermes --installer /path/to/install.sh
chattool setup hermes -e work --model openai/gpt-5.4-mini
chattool setup hermes --api-key sk-... --base-url https://api.example.com/v1 --model openai/gpt-5.4-mini
chattool setup hermes --install-only
```

如果检测到 `hermes` 命令或目标 `HERMES_HOME` 已存在，命令优先进入配置流程，不重复安装。`--install-only` 只安装/检查 ChatArch Hermes Agent，不写 `.env`、`config.yaml` 或 WebUI env。

## 配置写入

OpenAI-compatible 配置按以下优先级解析：

1. 显式 CLI 参数：`--api-key`、`--base-url`、`--model`
2. `-e/--env` 指定的 OpenAI `.env` 文件或 profile
3. 现有 `HERMES_HOME/.env` 与 `HERMES_HOME/config.yaml`
4. 当前 shell 环境变量
5. ChatTool 当前激活的 OpenAI typed env
6. 默认值：`https://api.openai.com/v1`、`gpt-5.4-mini`

写入位置：

- secrets 写入 `HERMES_HOME/.env`
- base URL / model 写入 `HERMES_HOME/config.yaml`

重复运行时只 patch 本次命令管理的 key，尽量保留未触达字段、注释和顺序。日志会显示 changed keys，但不会打印 secret value。

Feishu 不会默认导入。需要时显式传入：

```bash
chattool setup hermes --feishu-env rexwzh
```

## WebUI

独立 Hermes WebUI 需要已有 app files。ChatTool 不默认 clone WebUI 仓库。

生成 WebUI env：

```bash
chattool setup hermes --with-webui-env --webui-dir /path/to/hermes-webui
```

启动 WebUI：

```bash
chattool setup hermes --start-webui --webui-dir /path/to/hermes-webui
```

启动时使用 WebUI 原生入口：

1. `./ctl.sh start`
2. `./start.sh`
3. `python3 bootstrap.py`

WebUI 不是 npm 项目，`setup hermes` 不会执行 `npm install` 或前端 build。

默认 `--webui-host` 是 `127.0.0.1`。如果显式设置 `--webui-host 0.0.0.0`，必须同时设置 `--webui-password`。

## 验证命令

安装后建议执行：

```bash
hermes --help
hermes doctor
```

如果启动了 WebUI：

```bash
curl --noproxy '*' http://127.0.0.1:8787/health
```
