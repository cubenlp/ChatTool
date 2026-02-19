---
name: frp-configurator
description: "自动化 FRP (Fast Reverse Proxy) 部署。配置客户端/服务端，设置 Systemd 服务/Web UI，并为对应平台生成配对安装包。当用户想要设置 FRP、隧道或远程访问时调用。"
---

# FRP 配置器

本技能帮助您设置和管理 FRP (Fast Reverse Proxy)，以实现安全的内网穿透和远程访问。

## 功能

1.  **配置本地 (客户端)**: 在当前机器上安装并配置 `frpc`。
2.  **配置远程 (服务端)**: 在当前机器上安装并配置 `frps`。
3.  **配对 / 导出**:
    *   **导出到远程**: 如果您有客户端配置，生成匹配您密钥的服务端安装包。
    *   **导出到本地**: 如果您有服务端配置，生成匹配您密钥的客户端安装包。
4.  **卸载**: 移除 FRP 服务和配置。

## 工具 & 脚本

位于 `scripts/` 目录中：

*   `setup_client.sh`: 安装 `frpc`，设置 systemd 服务，配置 Web UI。
*   `setup_server.sh`: 安装 `frps`，设置 systemd 服务，配置仪表板。
*   `pack_for_server.sh`: 读取本地 `frpc.toml` $\rightarrow$ 生成 `frps_bundle.tar.gz`。
*   `pack_for_client.sh`: 读取本地 `frps.toml` $\rightarrow$ 生成 `frpc_bundle.tar.gz`。
*   `uninstall.sh`: 停止服务并移除 FRP 安装。

## 使用示例

### 1. 设置客户端 (本地)
```bash
# 交互式设置
bash scripts/setup_client.sh

# 非交互式 / 自动化设置 (推荐用于脚本)
# 这通过预先设置正确的服务器来避免“连接被拒绝”错误。
export FRP_SERVER_IP="x.x.x.x"     # 替换为您的服务器 IP
export FRP_SERVER_PORT="7000"      # 替换为您的服务器端口
export FRP_AUTH_TOKEN="my-secret-token" # 替换为您的 Token
bash scripts/setup_client.sh -y    # 使用 -y 跳过提示
```

### 2. 设置服务端 (远程)
```bash
# 交互式设置
bash scripts/setup_server.sh
```

### 3. 我有客户端，我需要设置服务端
```bash
# 基于我的客户端配置生成服务端安装包
bash scripts/pack_for_server.sh
# 然后上传 'frps_bundle.tar.gz' 到您的服务器并在其中运行安装脚本。
```

### 4. 我有服务端，我需要设置客户端
```bash
# 基于我的服务端配置生成客户端安装包
bash scripts/pack_for_client.sh
# 然后下载 'frpc_bundle.tar.gz' 到您的客户端机器并在其中运行安装脚本。
```

### 5. 卸载
```bash
bash scripts/uninstall.sh
```

## 配置详情

*   **默认安装路径**: `/srv/frp`
*   **配置文件**: `frpc.toml` / `frps.toml`
*   **Systemd 服务**: `frpc.service` / `frps.service`
*   **Web UI**:
    *   客户端管理: 端口 7555 (默认)
    *   服务端仪表板: 端口 7500 (默认)

## 故障排除

### 连接被拒绝 (client/service.go error)

如果在日志中看到类似 `connect to server error: dial tcp 127.0.0.1:7000: connect: connection refused` 的错误：
1.  **检查配置**: 确保 `/srv/frp/frpc.toml` 中的 `serverAddr` 指向您实际的远程服务器 IP，而不是 `127.0.0.1`。
2.  **检查日志**: `tail -f /srv/frp/frpc.log`
3.  **更新配置**:
    ```toml
    # /srv/frp/frpc.toml
    serverAddr = "YOUR_REMOTE_IP"
    serverPort = 7000 # 必须匹配服务端的 bindPort
    auth.token = "YOUR_AUTH_TOKEN" # 必须匹配服务端的 auth.token
    ```
4.  **重启服务**: `sudo systemctl restart frpc`

### 示例配置 (frpc.toml)

```toml
serverAddr = "203.0.113.10"
serverPort = 7000

auth.method = "token"
auth.token = "secure_token_123"

# 将本地 SSH (端口 22) 暴露给远程服务器 (端口 6000)
[[proxies]]
name = "ssh-my-laptop"
type = "tcp"
localIP = "127.0.0.1"
localPort = 22
remotePort = 6000
```
