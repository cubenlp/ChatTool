# OpenCode 配置（setup 命令）

OpenCode 使用 `opencode.json` 配置文件管理模型与提供商设置，ChatTool 提供 `setup opencode` 一键写入基础配置并安装 CLI。

## 1. 安装 Node.js

OpenCode CLI 通过 npm 安装，先确保已配置 Node.js：

```bash
chattool setup nodejs
```

该命令会直接写入 ChatTool 内置的 `nvm.sh`，不会再通过 `curl` 从 GitHub 拉取安装脚本。
默认会把 ChatTool 管理的 nvm 初始化块同步写入所有已探测到的 shell rc 文件（当前支持 `~/.zshrc` 和 `~/.bashrc`）；使用 `-i` 时可先交互选择要更新的 shell。
注意后续 `nvm install` 仍需要联网下载 Node.js 版本文件。
执行 `chattool setup opencode` 时，也会先检查本机是否已有 `Node.js >= 20` 和 `npm`；不满足且终端可交互时，会先提示是否安装/升级。

## 2. 交互式配置

```bash
chattool setup opencode
```

交互式模式会提示输入：

- `base_url`：OpenAI 兼容接口地址
- `api_key`：API Key（输入时会自动隐藏）
- `model`：默认模型名称（如 `gpt-4.1-mini`）

## 3. 非交互式配置

```bash
chattool setup opencode --base-url "https://example.com/openai" --api-key "sk-xxx" --model "gpt-4.1-mini"
chattool setup opencode --base-url "https://example.com/openai" --api-key "sk-xxx" --model "gpt-4.1-mini" --plugin auto-loop
```

如需更详细地查看依赖检测、npm 安装和配置写入阶段，可附加：

```bash
chattool setup opencode --log-level DEBUG
```

如果你已经在 `chatenv` 里维护了 OpenAI 配置，也可以显式复用：

```bash
chattool setup opencode -e work
chattool setup opencode -e ~/.config/chattool/envs/OpenAI/work.env
```

这里的 `-e/--env` 支持两种形式：

- `.env` 文件路径
- `OpenAI` 类型下保存过的 profile 名称，例如 `work`

解析顺序为：

1. 显式参数：`--base-url`、`--api-key`、`--model`
2. `-e/--env` 指定的 OpenAI 配置
3. 现有 `~/.config/opencode/opencode.json` 中的对应字段
4. 当前 shell 的系统环境变量（如 `OPENAI_API_BASE`）
5. `envs/OpenAI/.env` 中的 typed 默认值
6. 默认值

## 4. 可选插件预设

如果你希望在 OpenCode 配置里顺手启用现成的 `opencode-auto-loop` 插件，可显式附加：

```bash
chattool setup opencode --plugin auto-loop
```

该选项会把 `opencode-auto-loop` 追加写入 OpenCode 配置文件中的 `plugin` 数组；若已存在则不会重复追加。

## 5. 配置文件位置

配置默认写入：

```text
~/.config/opencode/opencode.json
```
