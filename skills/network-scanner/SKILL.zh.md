---
name: "network-scanner"
description: "使用 Ping 扫描和 TCP 端口扫描发现网段内的在线主机与开放服务。用户提到扫描网络、查找存活设备、检查开放端口、审计服务或梳理子网主机时使用。"
version: 0.1.0
---

# 网络扫描器

通过并发 ping 扫描和 TCP 端口扫描识别在线主机与开放服务。

## 工具

### `network_ping_scan`
通过 ICMP 回显请求扫描网段，查找存活主机。

**参数**：
- `network_segment`（必填）：CIDR 格式网段，例如 `10.0.0.0/24`
- `concurrency`（选填）：并发线程数，默认 `50`

### `network_port_scan`
检查一组主机上的指定 TCP 端口是否开放。

**参数**：
- `hosts`（必填）：要扫描的 IP 列表
- `port`（选填）：要检查的 TCP 端口，默认 `22`
- `concurrency`（选填）：并发线程数，默认 `50`

## 典型流程

### 扫描子网内所有在线设备
```python
active_hosts = network_ping_scan("192.168.1.0/24")
print(f"Found {len(active_hosts)} active devices: {active_hosts}")
```

### 查找子网中的 SSH 服务器
```python
# 第一步：先找在线主机
active_hosts = network_ping_scan("10.0.1.0/24")

# 第二步：只在在线主机上检查 22 端口
ssh_servers = network_port_scan(active_hosts, port=22)
print(f"SSH Servers: {ssh_servers}")
```

### 检查指定主机的 Web 服务端口
```python
targets = ["192.168.1.10", "192.168.1.11"]
web_servers = network_port_scan(targets, port=8080)
```

## 提示

- 先 `network_ping_scan`，再 `network_port_scan`，可以减少无效扫描。
- 如果扫描导致网络不稳定或丢包，降低 `concurrency`。
