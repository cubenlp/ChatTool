# Codex 配置（setup 命令）

## 1) 安装 nvm + Node.js

默认安装 LTS：

```bash
chattool setup nodejs
```

交互式选择版本：

```bash
chattool setup nodejs -i
```

## 2) 安装并配置 Codex

默认就是交互输入密钥：

```bash
chattool setup codex
```

如果你已经有变量，直接传参（可用 `--preferred-auth-method` 或 `--pam`）：

```bash
chattool setup codex --pam "cr_xxx"
```

## 3) 写入内容

命令会执行：

- 安装 `@openai/codex@latest`
- 写入 `~/.codex/config.toml`
- 写入 `~/.codex/auth.json`
- 将上述文件权限设置为 `600`

其中 `preferred_auth_method` 和 `OPENAI_API_KEY` 使用同一输入变量值。
默认不会在代码中内置明文密钥。
