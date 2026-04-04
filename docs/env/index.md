# Setup 模块

ChatTool 提供了一系列辅助工具的安装和配置功能。

## 功能列表

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

### Workspace 协作脚手架

使用 `setup workspace` 快速生成围绕核心项目的人类-AI 协作工作区骨架，默认采用 `reports/<task-name>/` 与 `playgrounds/<task-name>/` 的多任务并发结构。

```bash
chattool setup workspace
chattool setup workspace ~/workspace/demo
```

详细文档：[workspace.md](workspace.md)

### Lark CLI 配置

使用 `setup lark-cli` 快速安装官方 `lark-cli`，并复用 ChatTool 现有的 Feishu 配置。

```bash
chattool setup lark-cli
```

详细文档：[lark-cli.md](lark-cli.md)

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
