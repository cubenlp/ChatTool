# FRP 内网穿透配置

FRP (Fast Reverse Proxy) 是一个用于内网穿透的高性能反向代理工具。

## 功能

- 客户端 (FRP Client) 配置
- 服务端 (FRP Server) 配置
- 支持 SSH、VNC、Web 等多种服务类型

## 使用方法

```bash
# 启动 FRP 设置向导
chattool setup frp
```

该命令将启动交互式配置向导，引导你完成以下设置：

1. 选择角色：客户端或服务端
2. 配置服务器地址和端口
3. 配置待穿透的服务类型和端口
4. 生成配置文件

## 配置文件

配置文件通常位于 `~/frp/frpc.ini` (客户端) 或 `~/frp/frps.ini` (服务端)。

### 客户端配置示例

```ini
[common]
server_addr = your_server_ip
server_port = 7000

[ssh]
type = tcp
local_ip = 127.0.0.1
local_port = 22
remote_port = 6000

[web]
type = http
local_port = 8080
custom_domains = your.domain.com
```

### 服务端配置示例

```ini
[common]
bind_port = 7000
dashboard_port = 7500
token = your_token_here
```

## 启动服务

```bash
# 启动客户端
frpc -c ~/frp/frpc.ini

# 启动服务端
frps -c ~/frp/frps.ini
```

## 注意事项

- 确保服务器端口 (7000) 在防火墙中开放
- 使用强 token 保护 FRP 服务
- 建议使用 SSL/TLS 加密通信
