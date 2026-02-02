#!/bin/bash
set -e

# Configuration Defaults
FRP_VERSION="0.66.0"
FRP_ARCH="linux_amd64"
INSTALL_DIR="/srv/frp"
DEFAULT_SERVER_IP="127.0.0.1"
DEFAULT_SERVER_PORT="7000"
DEFAULT_WEB_PORT="7555"

# Check root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or sudo"
  exit 1
fi

echo ">>> Starting FRP Client Setup..."

# 1. Dependencies
echo ">>> Installing dependencies..."
if command -v apt-get &> /dev/null; then
    apt-get update && apt-get install -y wget tar pwgen
elif command -v yum &> /dev/null; then
    yum install -y wget tar pwgen
fi

# 2. Gather Info
read -p "Enter Server IP [${DEFAULT_SERVER_IP}]: " SERVER_IP
SERVER_IP=${SERVER_IP:-$DEFAULT_SERVER_IP}

read -p "Enter Server Port [${DEFAULT_SERVER_PORT}]: " SERVER_PORT
SERVER_PORT=${SERVER_PORT:-$DEFAULT_SERVER_PORT}

# Generate or Ask for Token
if command -v pwgen &> /dev/null; then
    GEN_TOKEN=$(pwgen -s 32 1)
else
    GEN_TOKEN=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 32)
fi

read -p "Enter Auth Token (Press Enter to generate new): " AUTH_TOKEN
AUTH_TOKEN=${AUTH_TOKEN:-$GEN_TOKEN}

# Web UI Credentials
if command -v pwgen &> /dev/null; then
    WEB_PASS=$(pwgen -s 16 1)
else
    WEB_PASS=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 16)
fi
WEB_USER="admin"

# 3. Prepare Directory
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# 4. Download FRP
FILE_NAME="frp_${FRP_VERSION}_${FRP_ARCH}.tar.gz"
if [ ! -f "$FILE_NAME" ]; then
    echo ">>> Downloading FRP v${FRP_VERSION}..."
    wget -c "https://github.com/fatedier/frp/releases/download/v${FRP_VERSION}/${FILE_NAME}"
fi

echo ">>> Extracting..."
tar -xzf "$FILE_NAME"
cp "frp_${FRP_VERSION}_${FRP_ARCH}/frpc" .
chmod +x frpc

# 5. Configure frpc.toml
echo ">>> Writing frpc.toml..."
cat > frpc.toml <<EOF
serverAddr = "${SERVER_IP}"
serverPort = ${SERVER_PORT}

# Web UI (Admin)
webServer.addr = "0.0.0.0"
webServer.port = ${DEFAULT_WEB_PORT}
webServer.user = "${WEB_USER}"
webServer.password = "${WEB_PASS}"

# Auth
auth.method = "token"
auth.token = "${AUTH_TOKEN}"

# Logging
log.to = "${INSTALL_DIR}/frpc.log"
log.level = "info"
log.maxDays = 3

# Example Proxy
# [[proxies]]
# name = "ssh-example"
# type = "tcp"
# localIP = "127.0.0.1"
# localPort = 22
# remotePort = 6000
EOF

# 6. Systemd
echo ">>> Configuring Systemd Service..."
cat > /etc/systemd/system/frpc.service <<EOF
[Unit]
Description=FRPC Client Service
After=network.target syslog.target
Wants=network.target

[Service]
Type=simple
ExecStart=${INSTALL_DIR}/frpc -c ${INSTALL_DIR}/frpc.toml
Restart=always
RestartSec=15s

[Install]
WantedBy=multi-user.target
EOF

# 7. Start
echo ">>> Starting Service..."
systemctl daemon-reload
systemctl enable frpc
systemctl restart frpc

echo "---------------------------------------------"
echo "✅ FRPC Setup Complete!"
echo "   Server: ${SERVER_IP}:${SERVER_PORT}"
echo "   Token:  ${AUTH_TOKEN}"
echo "   Web UI: http://localhost:${DEFAULT_WEB_PORT} (User: ${WEB_USER}, Pass: ${WEB_PASS})"
echo "---------------------------------------------"
