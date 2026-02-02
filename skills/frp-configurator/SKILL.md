---
name: frp-configurator
description: "Automates FRP (Fast Reverse Proxy) deployment. Configures Client/Server, sets up Systemd services/Web UI, and generates pairing installers for the counterpart platform. Invoke when user wants to setup FRP, tunneling, or remote access."
---

# FRP Configurator

This skill helps you set up and manage FRP (Fast Reverse Proxy) for secure intranet penetration and remote access.

## Capabilities

1.  **Configure Local (Client)**: Install and configure `frpc` on the current machine.
2.  **Configure Remote (Server)**: Install and configure `frps` on the current machine.
3.  **Pairing / Export**:
    *   **Export to Remote**: If you have a Client config, generate a Server installer package that matches your keys.
    *   **Export to Local**: If you have a Server config, generate a Client installer package that matches your keys.
4.  **Uninstall**: Remove FRP services and configuration.

## Tools & Scripts

Located in `scripts/`:

*   `setup_client.sh`: Installs `frpc`, sets up systemd service, configures Web UI.
*   `setup_server.sh`: Installs `frps`, sets up systemd service, configures Dashboard.
*   `pack_for_server.sh`: Reads local `frpc.toml` $\rightarrow$ Generates `frps_bundle.tar.gz`.
*   `pack_for_client.sh`: Reads local `frps.toml` $\rightarrow$ Generates `frpc_bundle.tar.gz`.
*   `uninstall.sh`: Stops services and removes FRP installation.

## Usage Examples

### 1. Setup Client (Local)
```bash
# Interactive setup
bash scripts/setup_client.sh
```

### 2. Setup Server (Remote)
```bash
# Interactive setup
bash scripts/setup_server.sh
```

### 3. I have a Client, I need to setup the Server
```bash
# Generate server installer based on my client config
bash scripts/pack_for_server.sh
# Then upload 'frps_bundle.tar.gz' to your server and run the install script inside.
```

### 4. I have a Server, I need to setup a Client
```bash
# Generate client installer based on my server config
bash scripts/pack_for_client.sh
# Then download 'frpc_bundle.tar.gz' to your client machine and run the install script inside.
```

### 5. Uninstall
```bash
bash scripts/uninstall.sh
```

## Configuration Details

*   **Default Install Path**: `/srv/frp`
*   **Config Files**: `frpc.toml` / `frps.toml`
*   **Systemd Services**: `frpc.service` / `frps.service`
*   **Web UI**:
    *   Client Admin: Port 7555 (default)
    *   Server Dashboard: Port 7500 (default)
