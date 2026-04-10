# Codex 配置（setup 命令）

## 1) 安装 nvm + Node.js

默认安装 LTS：

```bash
chattool setup nodejs
```

`chattool setup nodejs` 现在会直接写入内置的 `nvm.sh`，不再通过 `curl` 访问 GitHub 获取安装脚本。
默认会把 ChatTool 管理的 nvm 初始化块同步写入所有已探测到的 shell rc 文件（当前支持 `~/.zshrc` 和 `~/.bashrc`）；使用 `-i` 时可先交互选择要更新的 shell。
后续的 `nvm install` 仍会联网下载 Node.js 本体。

交互式选择版本：

```bash
chattool setup nodejs -i
```

如需更详细地查看 runtime 检测、shell rc 更新和 `nvm install` 阶段，可附加：

```bash
chattool setup nodejs --log-level DEBUG
```

## 2) 安装并配置 Codex

默认就是交互输入密钥：

```bash
chattool setup codex
```

命令会先检查本机是否已有 `Node.js >= 20` 和 `npm`。如果当前终端可交互且依赖不满足，会先提示是否执行 `chattool setup nodejs` 进行安装或升级。

如果你已经有变量，直接传 API key：

```bash
chattool setup codex --api-key "sk-xxx"
```

如果你已经在 `chatenv` 里维护了 `oai/openai` 配置，也可以显式复用：

```bash
chattool setup codex -e work
chattool setup codex -e ~/.config/chattool/envs/OpenAI/work.env
```

这里的 `-e/--env` 支持两种形式：

- `.env` 文件路径
- `OpenAI` 类型下保存过的 profile 名称，例如 `work`

解析顺序为：

1. 显式参数：`--api-key`、`--base-url`、`--model`
2. `-e/--env` 指定的 OpenAI 配置
3. 现有 `~/.codex/` 配置
4. 当前 shell 的系统环境变量（如 `OPENAI_API_BASE`）
5. `envs/OpenAI/.env` 中的 typed 默认值
6. 内置默认值

可选覆盖 `base_url` 和默认模型：

```bash
chattool setup codex --api-key "sk-xxx" --base-url "https://example.com/openai" --model "gpt-5.4"
```

如需更详细地查看依赖检测、npm 安装和配置写入阶段，可附加 `--log-level DEBUG`。

## 3) 写入内容

命令会执行：

- 安装 `@openai/codex@latest`
- 写入 `~/.codex/config.toml`
- 写入 `~/.codex/auth.json`
- 将上述文件权限设置为 `600`

其中：

- `config.toml` 中的 `preferred_auth_method` 固定写为 `"apikey"`
- 实际密钥只写入 `auth.json` 的 `OPENAI_API_KEY`

默认不会在代码中内置明文密钥。
