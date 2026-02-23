---
name: "network-scanner"
description: "专业的网络扫描工具，用于发现网段内的存活主机及开放端口。"
---

# 网络扫描器 (Network Scanner)

网络扫描器技能提供了基础的网络发现能力，允许你识别指定网络范围内的存活主机并检查开放的服务（端口）。这对于网络管理、安全审计和服务发现非常有用。

## 核心能力

- **Ping 扫描 (存活主机发现)**:
  - 使用 ICMP 回显请求扫描指定的网段 (CIDR 格式，例如 `192.168.1.0/24`)。
  - 快速识别当前在线 (Active) 的 IP 地址。
  - 支持高并发扫描，能够快速处理大型子网。

- **端口扫描 (服务发现)**:
  - 扫描目标 IP 地址列表以检测特定的 TCP 端口是否开放。
  - 适用于查找运行特定服务的机器 (例如端口 22 上的 SSH，端口 80/443 上的 Web 服务)。
  - 通常与 Ping 扫描结合使用：先发现存活主机，再检查具体服务。

## 可用工具

### `network_ping_scan`
扫描网段以查找存活主机。

- **参数**:
  - `network_segment` (必填): 目标网段，使用 CIDR 格式 (例如 `10.0.0.0/24`)。
  - `concurrency` (选填): 并发线程数 (默认: 50)。数值越高扫描越快，但资源消耗也会增加。

### `network_port_scan`
检查主机列表中的特定端口是否开放。

- **参数**:
  - `hosts` (必填): 需要扫描的 IP 地址列表。
  - `port` (选填): 要检查的 TCP 端口号 (默认: 22)。
  - `concurrency` (选填): 并发线程数 (默认: 50)。

## 使用场景示例

### 场景 1: 发现局域网内的所有活跃设备
"扫描 192.168.1.0/24 网段，看看哪些设备在线。"

```python
active_hosts = network_ping_scan("192.168.1.0/24")
print(f"发现了 {len(active_hosts)} 个活跃设备: {active_hosts}")
```

### 场景 2: 查找所有 SSH 服务器
"找出 10.0.1.0/24 子网内所有开放了 SSH 服务的服务器。"

```python
# 第一步: 先查找存活主机，节省扫描时间
active_hosts = network_ping_scan("10.0.1.0/24")

# 第二步: 在存活主机上检查端口 22
ssh_servers = network_port_scan(active_hosts, port=22)
print(f"SSH 服务器列表: {ssh_servers}")
```

### 场景 3: 检查特定服务器列表的 Web 服务
"检查 192.168.1.10 和 192.168.1.11 是否开放了 8080 端口。"

```python
targets = ["192.168.1.10", "192.168.1.11"]
web_servers = network_port_scan(targets, port=8080)
```
