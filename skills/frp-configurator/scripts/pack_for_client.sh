#!/bin/bash
set -e

# Configuration
INSTALL_DIR="/srv/frp"
SERVER_CONFIG="${INSTALL_DIR}/frps.toml"
BUNDLE_DIR="frpc_bundle"
FRP_VERSION="0.66.0"
FRP_ARCH="linux_amd64"

# Check root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or sudo"
  exit 1
fi

if [ ! -f "$SERVER_CONFIG" ]; then
    echo "Error: Local config $SERVER_CONFIG not found."
    exit 1
fi

echo ">>> Reading Local Server Config..."
BIND_PORT=$(grep "bindPort" "$SERVER_CONFIG" | awk -F'=' '{print $2}' | tr -d ' "')
AUTH_TOKEN=$(grep "auth.token" "$SERVER_CONFIG" | awk -F'=' '{print $2}' | tr -d ' "')

if [ -z "$BIND_PORT" ] || [ -z "$AUTH_TOKEN" ]; then
    echo "Error: Could not parse bindPort or auth.token from config."
    exit 1
fi

# Need External IP
read -p "Enter External IP of this server: " SERVER_IP
if [ -z "$SERVER_IP" ]; then
    echo "Error: IP required."
    exit 1
fi

echo ">>> Preparing Client Bundle..."
rm -rf "$BUNDLE_DIR"
mkdir -p "$BUNDLE_DIR"

# Get Binary
if [ -f "${INSTALL_DIR}/frp_${FRP_VERSION}_${FRP_ARCH}/frpc" ]; then
    cp "${INSTALL_DIR}/frp_${FRP_VERSION}_${FRP_ARCH}/frpc" "$BUNDLE_DIR/"
else
    FILE_NAME="frp_${FRP_VERSION}_${FRP_ARCH}.tar.gz"
    if [ ! -f "$FILE_NAME" ]; then
        wget -c "https://github.com/fatedier/frp/releases/download/v${FRP_VERSION}/${FILE_NAME}"
    fi
    tar -xzf "$FILE_NAME"
    cp "frp_${FRP_VERSION}_${FRP_ARCH}/frpc" "$BUNDLE_DIR/"
fi

# Generate frpc.toml
WEB_PASS=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 16)

cat > "$BUNDLE_DIR/frpc.toml" <<EOF
serverAddr = "${SERVER_IP}"
serverPort = ${BIND_PORT}

webServer.addr = "0.0.0.0"
webServer.port = 7555
webServer.user = "admin"
webServer.password = "${WEB_PASS}"

auth.method = "token"
auth.token = "${AUTH_TOKEN}"

log.to = "/srv/frp/frpc.log"
log.level = "info"
log.maxDays = 3

# Add proxies here
# [[proxies]]
# name = "ssh"
# type = "tcp"
# localIP = "127.0.0.1"
# localPort = 22
# remotePort = 6000
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
cp frpc "\$INSTALL_DIR/"
cp frpc.toml "\$INSTALL_DIR/"
chmod +x "\$INSTALL_DIR/frpc"

cat > /etc/systemd/system/frpc.service <<SERVICE
[Unit]
Description=FRP Client Service
After=network.target
[Service]
ExecStart=\${INSTALL_DIR}/frpc -c \${INSTALL_DIR}/frpc.toml
Restart=always
[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable frpc
systemctl restart frpc
echo "✅ Installed! Admin UI: http://localhost:7555 (User: admin, Pass: ${WEB_PASS})"
EOF
chmod +x "$BUNDLE_DIR/install.sh"

# Pack
tar -czf frpc_bundle.tar.gz "$BUNDLE_DIR"
echo "✅ Created frpc_bundle.tar.gz"
echo "   Download this to your client and run './install.sh' inside the extracted folder."
