# OpenCode 配置（setup 命令）

OpenCode 使用 `opencode.json` 配置文件管理模型与提供商设置，ChatTool 提供 `setup opencode` 一键写入基础配置并安装 CLI。

## 1. 安装 Node.js

OpenCode CLI 通过 npm 安装，先确保已配置 Node.js：

```bash
chattool setup nodejs
```

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
```

## 4. 配置文件位置

配置默认写入：

```text
~/.config/opencode/opencode.json
```
