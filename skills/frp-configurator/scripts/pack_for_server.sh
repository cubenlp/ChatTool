#!/bin/bash
set -e

# Configuration
INSTALL_DIR="/srv/frp"
CLIENT_CONFIG="${INSTALL_DIR}/frpc.toml"
BUNDLE_DIR="frps_bundle"
FRP_VERSION="0.66.0"
FRP_ARCH="linux_amd64"

# Check root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or sudo"
  exit 1
fi

if [ ! -f "$CLIENT_CONFIG" ]; then
    echo "Error: Local config $CLIENT_CONFIG not found."
    echo "Run setup_client.sh first or ensure frpc is installed."
    exit 1
fi

echo ">>> Reading Local Client Config..."
# Simple parsing (requires consistent formatting)
SERVER_PORT=$(grep "serverPort" "$CLIENT_CONFIG" | awk -F'=' '{print $2}' | tr -d ' "')
AUTH_TOKEN=$(grep "auth.token" "$CLIENT_CONFIG" | awk -F'=' '{print $2}' | tr -d ' "')

if [ -z "$SERVER_PORT" ] || [ -z "$AUTH_TOKEN" ]; then
    echo "Error: Could not parse serverPort or auth.token from config."
    exit 1
fi

echo "   Server Port: $SERVER_PORT"
echo "   Auth Token:  $AUTH_TOKEN"

echo ">>> Preparing Server Bundle..."
rm -rf "$BUNDLE_DIR"
mkdir -p "$BUNDLE_DIR"

# Get Binary
if [ -f "${INSTALL_DIR}/frp_${FRP_VERSION}_${FRP_ARCH}/frps" ]; then
    cp "${INSTALL_DIR}/frp_${FRP_VERSION}_${FRP_ARCH}/frps" "$BUNDLE_DIR/"
else
    # Try to download if missing
    FILE_NAME="frp_${FRP_VERSION}_${FRP_ARCH}.tar.gz"
    if [ ! -f "$FILE_NAME" ]; then
        wget -c "https://github.com/fatedier/frp/releases/download/v${FRP_VERSION}/${FILE_NAME}"
    fi
    tar -xzf "$FILE_NAME"
    cp "frp_${FRP_VERSION}_${FRP_ARCH}/frps" "$BUNDLE_DIR/"
fi

# Generate frps.toml
# Generate a random password for the dashboard in the bundle
DASH_PASS=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 16)

cat > "$BUNDLE_DIR/frps.toml" <<EOF
bindPort = ${SERVER_PORT}

webServer.addr = "0.0.0.0"
webServer.port = 7500
webServer.user = "admin"
webServer.password = "${DASH_PASS}"

auth.method = "token"
auth.token = "${AUTH_TOKEN}"

log.to = "/srv/frp/frps.log"
log.level = "info"
log.maxDays = 3
EOF

# Generate Install Script
cat > "$BUNDLE_DIR/install.sh" <<EOF
#!/bin/bash
set -e
INSTALL_DIR="/srv/frp"

if [ "\$EUID" -ne 0 ]; then
  echo "Run as root"
  exit 1
fi

mkdir -p "\$INSTALL_DIR"
cp frps "\$INSTALL_DIR/"
cp frps.toml "\$INSTALL_DIR/"
chmod +x "\$INSTALL_DIR/frps"

cat > /etc/systemd/system/frps.service <<SERVICE
[Unit]
Description=FRP Server Service
After=network.target
[Service]
ExecStart=\${INSTALL_DIR}/frps -c \${INSTALL_DIR}/frps.toml
Restart=always
[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable frps
systemctl restart frps
echo "✅ Installed! Dashboard Pass: ${DASH_PASS}"
EOF
chmod +x "$BUNDLE_DIR/install.sh"

# Pack
tar -czf frps_bundle.tar.gz "$BUNDLE_DIR"
echo "✅ Created frps_bundle.tar.gz"
echo "   Upload this to your server and run './install.sh' inside the extracted folder."
