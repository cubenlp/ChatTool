# Network Scanning

The Network Scanning module provides tools for discovering active hosts and open ports on a network.

## Tools

### `network_ping_scan`

Scans a network segment for active hosts using ICMP ping.

**Arguments:**

- `network_segment` (str): The network segment to scan in CIDR notation (e.g., `192.168.1.0/24`).
- `concurrency` (int, optional): The number of concurrent threads to use (default: 50).

**Returns:**

- `List[str]`: A list of active IP addresses found.

### `network_port_scan`

Scans a list of hosts for a specific open port.

**Arguments:**

- `hosts` (List[str]): A list of IP addresses to scan.
- `port` (int, optional): The port number to check (default: 22).
- `concurrency` (int, optional): The number of concurrent threads to use (default: 50).

**Returns:**

- `List[str]`: A list of hosts with the specified port open.
