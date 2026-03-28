# Codex 配置（setup 命令）

## 1) 安装 nvm + Node.js

默认安装 LTS：

```bash
chattool setup nodejs
```

`chattool setup nodejs` 现在会直接写入内置的 `nvm.sh`，不再通过 `curl` 访问 GitHub 获取安装脚本。
后续的 `nvm install` 仍会联网下载 Node.js 本体。

交互式选择版本：

```bash
chattool setup nodejs -i
```

## 2) 安装并配置 Codex

默认就是交互输入密钥：

```bash
chattool setup codex
```

命令会先检查本机是否已有 `Node.js >= 20` 和 `npm`。如果当前终端可交互且依赖不满足，会先提示是否执行 `chattool setup nodejs` 进行安装或升级。

如果你已经有变量，直接传 API key（可用 `--preferred-auth-method` 或 `--pam`，当前这两个开关实际承载的是 `OPENAI_API_KEY` 值）：

```bash
chattool setup codex --pam "sk-xxx"
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

1. 显式参数：`--pam`（OpenAI API key）、`--base-url`、`--model`
2. `-e/--env` 指定的 OpenAI 配置
3. 当前 `oai/openai` 生效配置
4. 现有 `~/.codex/` 配置
5. 内置默认值

可选覆盖 `base_url` 和默认模型：

```bash
chattool setup codex --pam "sk-xxx" --base-url "https://example.com/openai" --model "gpt-5.4"
```

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
