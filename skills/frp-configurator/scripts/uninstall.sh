#!/bin/bash
set -e

# Configuration
INSTALL_DIR="/srv/frp"

# Check root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or sudo"
  exit 1
fi

echo ">>> Starting FRP Uninstallation..."

# Function to remove service
remove_service() {
    SERVICE_NAME=$1
    if systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
        echo ">>> Found ${SERVICE_NAME} service. Stopping and disabling..."
        systemctl stop ${SERVICE_NAME} || true
        systemctl disable ${SERVICE_NAME} || true
        rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
        echo ">>> Removed /etc/systemd/system/${SERVICE_NAME}.service"
    else
        echo ">>> ${SERVICE_NAME} service not found."
    fi
}

# Remove Services
remove_service "frpc"
remove_service "frps"

# Reload Systemd
echo ">>> Reloading systemd daemon..."
systemctl daemon-reload

# Remove Files
if [ -d "$INSTALL_DIR" ]; then
    read -p ">>> Remove installation directory ${INSTALL_DIR}? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$INSTALL_DIR"
        echo ">>> Removed ${INSTALL_DIR}"
    else
        echo ">>> Skipped removing ${INSTALL_DIR}"
    fi
else
    echo ">>> Installation directory ${INSTALL_DIR} not found."
fi

echo "---------------------------------------------"
echo "✅ FRP Uninstallation Complete!"
echo "---------------------------------------------"
