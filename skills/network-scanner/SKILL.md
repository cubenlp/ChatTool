---
name: "network-scanner"
description: "Discover active hosts and open ports within a network segment using ping sweeps and TCP port scans. Use when the user asks to scan a network, find active devices, check open ports, audit services, or map hosts on a subnet."
version: 0.1.0
---

# Network Scanner

Identify active hosts and open services within a network range using concurrent ping sweeps and TCP port scans.

## Tools

### `network_ping_scan`
Scan a network segment to find active hosts via ICMP echo requests.

**Parameters**:
- `network_segment` (required): Target network in CIDR notation (e.g., `10.0.0.0/24`).
- `concurrency` (optional): Parallel threads (default: 50). Higher values scan faster but use more resources.

### `network_port_scan`
Check a list of hosts for a specific open TCP port.

**Parameters**:
- `hosts` (required): List of IP addresses to scan.
- `port` (optional): TCP port number to check (default: 22).
- `concurrency` (optional): Parallel threads (default: 50).

## Workflows

### Find all active devices on a subnet
```python
active_hosts = network_ping_scan("192.168.1.0/24")
print(f"Found {len(active_hosts)} active devices: {active_hosts}")
```

### Find all SSH servers on a subnet
```python
# Step 1: Discover live hosts
active_hosts = network_ping_scan("10.0.1.0/24")

# Step 2: Check port 22 on live hosts
ssh_servers = network_port_scan(active_hosts, port=22)
print(f"SSH Servers: {ssh_servers}")
```

### Check specific hosts for a web service port
```python
targets = ["192.168.1.10", "192.168.1.11"]
web_servers = network_port_scan(targets, port=8080)
```

## Tips

- Chain `network_ping_scan` → `network_port_scan` to limit port scan scope to live hosts only.
- Lower `concurrency` if the scan causes network instability or drops.
