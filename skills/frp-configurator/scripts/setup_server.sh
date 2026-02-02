#!/bin/bash
set -e

# Configuration Defaults
FRP_VERSION="0.66.0"
FRP_ARCH="linux_amd64"
INSTALL_DIR="/srv/frp"
DEFAULT_BIND_PORT="7000"
DEFAULT_DASH_PORT="7500"

# Check root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or sudo"
  exit 1
fi

echo ">>> Starting FRP Server Setup..."

# 1. Dependencies
echo ">>> Installing dependencies..."
if command -v apt-get &> /dev/null; then
    apt-get update && apt-get install -y wget tar pwgen
elif command -v yum &> /dev/null; then
    yum install -y wget tar pwgen
fi

# 2. Gather Info
read -p "Enter Bind Port [${DEFAULT_BIND_PORT}]: " BIND_PORT
BIND_PORT=${BIND_PORT:-$DEFAULT_BIND_PORT}

# Generate or Ask for Token
if command -v pwgen &> /dev/null; then
    GEN_TOKEN=$(pwgen -s 32 1)
else
    GEN_TOKEN=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 32)
fi

read -p "Enter Auth Token (Press Enter to generate new): " AUTH_TOKEN
AUTH_TOKEN=${AUTH_TOKEN:-$GEN_TOKEN}

# Dashboard Credentials
if command -v pwgen &> /dev/null; then
    DASH_PASS=$(pwgen -s 16 1)
else
    DASH_PASS=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 16)
fi
DASH_USER="admin"

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
cp "frp_${FRP_VERSION}_${FRP_ARCH}/frps" .
chmod +x frps

# 5. Configure frps.toml
echo ">>> Writing frps.toml..."
cat > frps.toml <<EOF
bindPort = ${BIND_PORT}

# Dashboard
webServer.addr = "0.0.0.0"
webServer.port = ${DEFAULT_DASH_PORT}
webServer.user = "${DASH_USER}"
webServer.password = "${DASH_PASS}"

# Auth
auth.method = "token"
auth.token = "${AUTH_TOKEN}"

# Logging
log.to = "${INSTALL_DIR}/frps.log"
log.level = "info"
log.maxDays = 3
EOF

# 6. Systemd
echo ">>> Configuring Systemd Service..."
cat > /etc/systemd/system/frps.service <<EOF
[Unit]
Description=FRP Server Service
After=network.target syslog.target
Wants=network.target

[Service]
Type=simple
ExecStart=${INSTALL_DIR}/frps -c ${INSTALL_DIR}/frps.toml
Restart=always
RestartSec=15s

[Install]
WantedBy=multi-user.target
EOF

# 7. Start
echo ">>> Starting Service..."
systemctl daemon-reload
systemctl enable frps
systemctl restart frps

echo "---------------------------------------------"
echo "✅ FRPS Setup Complete!"
echo "   Bind Port: ${BIND_PORT}"
echo "   Token:     ${AUTH_TOKEN}"
echo "   Dashboard: http://<Server-IP>:${DEFAULT_DASH_PORT} (User: ${DASH_USER}, Pass: ${DASH_PASS})"
echo "---------------------------------------------"
