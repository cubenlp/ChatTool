# 网络扫描

`chattool` 提供网络扫描工具，支持 Ping 扫描和端口扫描，同时提供 MCP 接口供 LLM 客户端调用。

## CLI

```bash
chattool client network [COMMAND] [OPTIONS]
```

### Ping 扫描

```bash
chattool client network ping --network 192.168.1.0/24 --output active_hosts.txt
```

| 参数 | 说明 |
|------|------|
| `--network / -net` | 扫描网段（CIDR），必填 |
| `--concurrency / -n` | 并发线程数（默认 50） |
| `--output / -o` | 结果保存路径 |

### 端口扫描

```bash
# 扫描网段的 SSH 端口
chattool client network ssh --network 192.168.1.0/24 --output ssh_hosts.txt

# 扫描指定 IP 列表的自定义端口
chattool client network ssh --input active_hosts.txt --port 8080
```

| 参数 | 说明 |
|------|------|
| `--network / -net` | 扫描网段（与 `--input` 二选一） |
| `--input / -i` | IP 列表文件（与 `--network` 二选一） |
| `--port / -p` | 扫描端口（默认 22） |
| `--concurrency / -n` | 并发线程数（默认 50） |
| `--output / -o` | 结果保存路径 |

## MCP 工具

### `network_ping_scan`

扫描网段内的活跃主机。

| 参数 | 类型 | 说明 |
|------|------|------|
| `network_segment` | str | CIDR 格式网段，如 `192.168.1.0/24` |
| `concurrency` | int | 并发线程数（默认 50） |

返回活跃 IP 列表。

### `network_port_scan`

扫描主机列表的指定端口。

| 参数 | 类型 | 说明 |
|------|------|------|
| `hosts` | List[str] | IP 地址列表 |
| `port` | int | 端口号（默认 22） |
| `concurrency` | int | 并发线程数（默认 50） |

返回端口开放的主机列表。
