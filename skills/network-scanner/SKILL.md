---
name: "network-scanner"
description: "Professional network scanning utility for discovering active hosts and open ports within a network segment."
---

# Network Scanner

The Network Scanner skill provides essential network discovery capabilities, allowing you to identify active hosts and check for open services (ports) within a specified network range. This is useful for network administration, security auditing, and service discovery.

## Capabilities

- **Ping Sweep (Active Host Discovery)**: 
  - Scans a specified network segment (CIDR notation, e.g., `192.168.1.0/24`) using ICMP echo requests.
  - Identifies which IP addresses are currently active (online).
  - Supports high concurrency for fast scanning of large subnets.

- **Port Scanning (Service Discovery)**:
  - Scans a list of target IP addresses for a specific open TCP port.
  - Useful for finding machines running specific services (e.g., SSH on port 22, Web on port 80/443).
  - Can be chained with the Ping Sweep to first find active hosts and then check for services.

## Tools

### `network_ping_scan`
Scans a network segment to find active hosts.

- **Parameters**:
  - `network_segment` (required): The target network in CIDR notation (e.g., `10.0.0.0/24`).
  - `concurrency` (optional): Number of parallel threads to use (default: 50). Higher values are faster but consume more system resources.

### `network_port_scan`
Checks a list of hosts for a specific open port.

- **Parameters**:
  - `hosts` (required): A list of IP addresses to scan.
  - `port` (optional): The TCP port number to check (default: 22).
  - `concurrency` (optional): Number of parallel threads (default: 50).

## Usage Examples

### Scenario 1: Find all active devices on the local network
"Scan the 192.168.1.0/24 network to see which devices are online."

```python
active_hosts = network_ping_scan("192.168.1.0/24")
print(f"Found {len(active_hosts)} active devices: {active_hosts}")
```

### Scenario 2: Find all SSH servers
"Find all servers with SSH open in the 10.0.1.0/24 subnet."

```python
# Step 1: Find active hosts first to save time
active_hosts = network_ping_scan("10.0.1.0/24")

# Step 2: Check port 22 on active hosts
ssh_servers = network_port_scan(active_hosts, port=22)
print(f"SSH Servers: {ssh_servers}")
```

### Scenario 3: Check a specific list of servers for a web service
"Check if 192.168.1.10 and 192.168.1.11 have port 8080 open."

```python
targets = ["192.168.1.10", "192.168.1.11"]
web_servers = network_port_scan(targets, port=8080)
```
