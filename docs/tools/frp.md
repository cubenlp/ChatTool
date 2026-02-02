# FRP 内网穿透工具

FRP (Fast Reverse Proxy) 是一个专注于内网穿透的高性能的反向代理应用，支持 TCP、UDP、HTTP、HTTPS 等多种协议。

ChatTool 提供了一套自动化脚本，帮助你快速部署和配置 FRP，支持**本地配置**、**远程配置**以及**配置同步（Pairing）**。

## 核心功能

ChatTool 的 FRP 技能 (`frp-configurator`) 提供了以下核心能力：

1.  **一键部署客户端 (Client)**：在本地机器上安装并配置 `frpc`。
2.  **一键部署服务端 (Server)**：在云服务器上安装并配置 `frps`。
3.  **配置配对 (Pairing)**：
    *   **基于客户端生成服务端**：如果你已经配置好了客户端，可以一键生成对应的服务端安装包。
    *   **基于服务端生成客户端**：如果你已经配置好了服务端，可以一键生成对应的客户端安装包。

## 快速开始

脚本位于项目的 `skills/frp-configurator/scripts/` 目录下。

### 场景一：全新部署

如果你是第一次使用，建议先部署服务端，再部署客户端。

**1. 在云服务器上部署服务端：**

```bash
sudo bash skills/frp-configurator/scripts/setup_server.sh
```

按照提示输入绑定端口（默认 7000）和 Token。

**2. 在本地机器上部署客户端：**

```bash
sudo bash skills/frp-configurator/scripts/setup_client.sh
```

按照提示输入服务器 IP、端口和 Token。

### 场景二：已有客户端，部署服务端

如果你已经在本地配置好了 `frpc.toml`，希望快速部署一个匹配的服务端：

1.  在本地运行打包脚本：
    ```bash
    sudo bash skills/frp-configurator/scripts/pack_for_server.sh
    ```
2.  脚本会生成 `frps_bundle.tar.gz`。
3.  将该文件上传到服务器。
4.  在服务器上解压并运行安装：
    ```bash
    tar -xzf frps_bundle.tar.gz
    cd frps_bundle
    sudo ./install.sh
    ```

### 场景三：已有服务端，添加新客户端

如果你已经有一个运行中的 FRPS 服务端，希望配置一个新的客户端连接它：

1.  在服务端运行打包脚本：
    ```bash
    sudo bash skills/frp-configurator/scripts/pack_for_client.sh
    ```
2.  输入服务器的公网 IP。
3.  脚本会生成 `frpc_bundle.tar.gz`。
4.  将该文件下载到客户端机器。
5.  在客户端上解压并运行安装：
    ```bash
    tar -xzf frpc_bundle.tar.gz
    cd frpc_bundle
    sudo ./install.sh
    ```

## 卸载

如果需要移除 FRP 服务和配置：

```bash
sudo bash skills/frp-configurator/scripts/uninstall.sh
```

脚本会：
1. 停止并禁用 `frpc` 和 `frps` 服务。
2. 删除 Systemd 服务文件。
3. 询问是否删除安装目录（默认 `/srv/frp`）。

## 配置说明

### 目录结构

默认安装路径为 `/srv/frp`。

*   **客户端**：`/srv/frp/frpc` (二进制), `/srv/frp/frpc.toml` (配置), `/srv/frp/frpc.log` (日志)
*   **服务端**：`/srv/frp/frps` (二进制), `/srv/frp/frps.toml` (配置), `/srv/frp/frps.log` (日志)

### Web 管理界面

脚本会自动配置 Web 管理界面（Dashboard）：

*   **服务端 Dashboard**：默认端口 `7500`。
    *   访问：`http://<Server-IP>:7500`
    *   账号：`admin`
    *   密码：随机生成（安装时会显示，或查看配置文件）
*   **客户端 Admin UI**：默认端口 `7555`。
    *   访问：`http://localhost:7555`
    *   账号：`admin`
    *   密码：随机生成

### Systemd 服务

安装后会自动创建 Systemd 服务，支持开机自启：

*   `systemctl status frpc` (客户端)
*   `systemctl status frps` (服务端)
