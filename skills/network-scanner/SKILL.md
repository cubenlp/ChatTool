---
name: "network-scanner"
description: "Network scanning utilities including Ping Sweep and Port Scanning."
---

# Network Scanner

This skill provides network scanning capabilities to discover active hosts and open ports.

## Capabilities

- **Ping Scan**: Scan a network segment (CIDR) to find active hosts using ICMP ping.
- **Port Scan**: Scan specific ports on a list of hosts to check for open services (e.g., SSH).

## Tools

- `network_ping_scan`: Scan a network segment for active hosts.
- `network_port_scan`: Scan a list of hosts for a specific open port.

## Usage Examples

### Ping Scan
Scan the local network `192.168.1.0/24`:
```python
active_hosts = network_ping_scan("192.168.1.0/24")
```

### Port Scan
Check if SSH (port 22) is open on a list of hosts:
```python
open_hosts = network_port_scan(["192.168.1.10", "192.168.1.11"], port=22)
```
