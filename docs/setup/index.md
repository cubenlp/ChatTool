# Setup 模块

ChatTool 提供了一系列辅助工具的安装和配置功能。

## 功能列表

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
