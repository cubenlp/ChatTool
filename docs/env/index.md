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
chattool setup opencode --install-only
```

详细文档：[opencode.md](opencode.md)

### Docker 环境检查

使用 `setup docker` 检查 Docker / Docker Compose / docker 组状态。

```bash
chattool setup docker
chattool setup docker --sudo -i
```

详细文档：[docker.md](docker.md)

### Workspace 协作脚手架

使用 `setup workspace` 快速生成围绕核心项目的人类-AI 协作工作区骨架。当前默认采用 `projects/` 为中心的最小 `PRD.md` project 执行模型，需要更复杂层级时再按项目自己的 `PRD.md` 自然演化。

```bash
chattool setup workspace
chattool setup workspace ~/workspace/demo
chattool setup workspace ~/workspace/demo --with-opencode-loop
chattool setup opencode --install-only --plugin chatloop
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

```bash
chattool nginx --list
chattool nginx -i
```

详细文档：[nginx_proxy.md](nginx_proxy.md)
