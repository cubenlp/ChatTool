# Network Scanning Tools

The `chattool` CLI provides commands for network scanning, allowing you to quickly discover active hosts and open ports directly from the terminal.

## Usage

The network tools are available under the `network` command group.

```bash
chattool client network [COMMAND] [OPTIONS]
```

### Ping Scan

Scan a network segment for active hosts using ICMP ping.

```bash
chattool client network ping --network <CIDR> [OPTIONS]
```

**Options:**

- `--network`, `-net`: The network segment to scan (e.g., `192.168.1.0/24`). **Required**.
- `--concurrency`, `-n`: Number of concurrent threads (default: 50).
- `--output`, `-o`: Path to save the list of active IPs.

**Example:**

```bash
chattool client network ping --network 192.168.1.0/24 --output active_hosts.txt
```

### Port Scan (SSH)

Scan for open ports (defaulting to SSH/22) on a list of IPs or a network segment.

```bash
chattool client network ssh [OPTIONS]
```

**Options:**

- `--input`, `-i`: Input file containing a list of IPs to scan.
- `--network`, `-net`: Network segment to scan (alternative to input file).
- `--port`, `-p`: Port to scan (default: 22).
- `--concurrency`, `-n`: Number of concurrent threads (default: 50).
- `--output`, `-o`: Path to save the list of hosts with open ports.

**Note:** You must provide either `--input` or `--network`.

**Examples:**

Scan a network for SSH (port 22):
```bash
chattool client network ssh --network 192.168.1.0/24 --output ssh_hosts.txt
```

Scan a list of IPs from a file for a custom port:
```bash
chattool client network ssh --input active_hosts.txt --port 8080
```
