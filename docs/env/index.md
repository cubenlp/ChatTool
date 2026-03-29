# Setup 模块

ChatTool 提供了一系列辅助工具的安装和配置功能。

## 功能列表

### uv 配置

使用 `setup uv` 把当前 Python 项目切到 `uv` 工作流。

```bash
chattool setup uv
```

详细文档：[uv.md](uv.md)

### Codex 配置

使用 `setup codex` 快速安装并写入配置。

```bash
chattool setup codex
```

详细文档：[codex.md](codex.md)

### Claude Code 配置

使用 `setup claude` 快速安装 Claude Code 并写入配置。

```bash
chattool setup claude
```

### OpenCode 配置

使用 `setup opencode` 快速安装并写入配置。

```bash
chattool setup opencode
```

详细文档：[opencode.md](opencode.md)

### Lark CLI 配置

使用 `setup lark-cli` 快速安装官方 `lark-cli`，并复用 ChatTool 现有的 Feishu 配置。

```bash
chattool setup lark-cli
```

详细文档：[lark-cli.md](lark-cli.md)

### Playground 工作区初始化

使用 `setup playground` 初始化或更新一个工作区，并按需把 clone 下来的 `ChatTool/` 项目继续接入 `uv`。

```bash
chattool setup playground
chattool setup playground --uv
```

详细文档：参见 [client.md](../client.md) 中的 `setup playground` 章节。

### Chrome 浏览器驱动安装

自动安装 Chrome 和 Chromedriver。

```bash
# 交互式安装
chattool setup chrome -i

# 自动安装
chattool setup chrome
```

详细文档：[chrome.md](chrome.md)

### FRP 内网穿透

FRP (Fast Reverse Proxy) 客户端/服务端配置工具。

```bash
chattool setup frp
```

详细文档：[frp.md](frp.md) (TODO)

### Nginx 反向代理

Nginx 反向代理配置指南。

详细文档：[nginx_proxy.md](nginx_proxy.md)
