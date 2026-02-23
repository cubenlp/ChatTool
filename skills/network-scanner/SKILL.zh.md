---
name: "network-scanner"
description: "网络扫描工具，包括 Ping 扫描和端口扫描。"
---

# 网络扫描器 (Network Scanner)

本技能提供网络扫描能力，用于发现存活主机和开放端口。

## 能力

- **Ping 扫描**: 扫描网段 (CIDR) 以发现使用 ICMP ping 的存活主机。
- **端口扫描**: 扫描主机列表上的特定端口以检查开放服务 (例如 SSH)。

## 工具

- `network_ping_scan`: 扫描网段以查找存活主机。
- `network_port_scan`: 扫描主机列表以查找特定开放端口。

## 使用示例

### Ping 扫描
扫描本地网络 `192.168.1.0/24`:
```python
active_hosts = network_ping_scan("192.168.1.0/24")
```

### 端口扫描
检查主机列表上的 SSH (端口 22) 是否开放:
```python
open_hosts = network_port_scan(["192.168.1.10", "192.168.1.11"], port=22)
```
