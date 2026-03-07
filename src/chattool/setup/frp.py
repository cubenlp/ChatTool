import os
import sys
import shutil
import tarfile
import tempfile
import subprocess
import platform
from pathlib import Path
from chattool.utils.tui import ask_with_escape_back, get_style, BACK_VALUE

FRP_VERSION_DEFAULT = "0.66.0"

def get_system_arch():
    arch = platform.machine()
    if arch == 'x86_64':
        return 'amd64'
    elif arch == 'aarch64':
        return 'arm64'
    elif arch == 'armv7l':
        return 'arm'
    else:
        return arch

def download_file(url, dest_path):
    import requests
    print(f"Downloading from {url}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print("Download complete.")

def extract_frp(archive_path, extract_to, binary_name):
    print(f"Extracting {archive_path}...")
    with tarfile.open(archive_path, "r:gz") as tar:
        # Find the binary in the archive
        member = None
        for m in tar.getmembers():
            if m.name.endswith(f"/{binary_name}"):
                member = m
                break
        
        if not member:
            raise ValueError(f"Could not find {binary_name} in archive")
        
        # Extract only the binary
        member.name = os.path.basename(member.name) # Extract to current dir structure
        tar.extract(member, path=extract_to)
        
    extracted_bin = os.path.join(extract_to, binary_name)
    os.chmod(extracted_bin, 0o755)
    return extracted_bin

def setup_frp():
    import questionary
    style = get_style()

    # 1. Ask Mode
    mode = ask_with_escape_back(
        questionary.select(
            "Select FRP Mode:",
            choices=["Client", "Server"],
            style=style
        )
    )
    if mode == BACK_VALUE: return
    
    is_server = mode == "Server"
    binary_name = "frps" if is_server else "frpc"
    config_name = "frps.toml" if is_server else "frpc.toml"

    # 2. Ask Install Method
    install_method = ask_with_escape_back(
        questionary.select(
            "Select Installation Method:",
            choices=["Download", "Local File"],
            style=style
        )
    )
    if install_method == BACK_VALUE: return

    work_dir = Path.home() / ".frp"
    work_dir.mkdir(parents=True, exist_ok=True)
    
    final_bin_path = work_dir / binary_name

    if install_method == "Download":
        version = ask_with_escape_back(
            questionary.text(
                "Enter FRP Version:",
                default=FRP_VERSION_DEFAULT,
                style=style
            )
        )
        if version == BACK_VALUE: return

        arch = get_system_arch()
        os_name = platform.system().lower()
        filename = f"frp_{version}_{os_name}_{arch}.tar.gz"
        download_url = f"https://github.com/fatedier/frp/releases/download/v{version}/{filename}"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = os.path.join(tmpdir, filename)
            try:
                download_file(download_url, archive_path)
                extracted_bin = extract_frp(archive_path, tmpdir, binary_name)
                shutil.copy2(extracted_bin, final_bin_path)
            except Exception as e:
                print(f"Error downloading/extracting: {e}")
                return

    else: # Local File
        local_path = ask_with_escape_back(
            questionary.path(
                "Enter path to local FRP archive (tar.gz):",
                style=style
            )
        )
        if local_path == BACK_VALUE: return
        
        if not os.path.exists(local_path):
            print("File not found.")
            return

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                extracted_bin = extract_frp(local_path, tmpdir, binary_name)
                shutil.copy2(extracted_bin, final_bin_path)
            except Exception as e:
                print(f"Error extracting: {e}")
                return

    print(f"FRP binary installed at: {final_bin_path}")

    # 3. Configure
    config_content = ""
    
    if is_server:
        bind_port = ask_with_escape_back(
            questionary.text("Enter Bind Port:", default="7000", style=style)
        )
        if bind_port == BACK_VALUE: return
        
        token = ask_with_escape_back(
            questionary.text("Enter Authentication Token:", style=style)
        )
        if token == BACK_VALUE: return
        
        dashboard_port = ask_with_escape_back(
            questionary.text("Enter Dashboard Port (optional, press Enter to skip):", default="7500", style=style)
        )
        if dashboard_port == BACK_VALUE: return
        
        dashboard_user = "admin"
        dashboard_pwd = "admin"
        
        if dashboard_port:
            dashboard_user = ask_with_escape_back(
                questionary.text("Enter Dashboard User:", default="admin", style=style)
            )
            if dashboard_user == BACK_VALUE: return
            
            dashboard_pwd = ask_with_escape_back(
                questionary.text("Enter Dashboard Password:", default="admin", style=style)
            )
            if dashboard_pwd == BACK_VALUE: return

        config_content = f"""bindPort = {bind_port}
auth.token = "{token}"

"""
        if dashboard_port:
            config_content += f"""
webServer.addr = "0.0.0.0"
webServer.port = {dashboard_port}
webServer.user = "{dashboard_user}"
webServer.password = "{dashboard_pwd}"
"""

    else: # Client
        server_addr = ask_with_escape_back(
            questionary.text("Enter Server IP/Domain:", style=style)
        )
        if server_addr == BACK_VALUE: return
        
        server_port = ask_with_escape_back(
            questionary.text("Enter Server Port:", default="7000", style=style)
        )
        if server_port == BACK_VALUE: return
        
        token = ask_with_escape_back(
            questionary.text("Enter Authentication Token:", style=style)
        )
        if token == BACK_VALUE: return

        config_content = f"""serverAddr = "{server_addr}"
serverPort = {server_port}
auth.token = "{token}"

# Add your proxies here
# [[proxies]]
# name = "ssh"
# type = "tcp"
# localIP = "127.0.0.1"
# localPort = 22
# remotePort = 6000
"""

    config_path = work_dir / config_name
    with open(config_path, "w") as f:
        f.write(config_content)
    
    print(f"Configuration saved to: {config_path}")

    # 4. Systemd Service
    service_name = f"frp-{mode.lower()}"
    service_content = f"""[Unit]
Description=FRP {mode} Service
After=network.target

[Service]
Type=simple
User={os.environ.get('USER', 'root')}
ExecStart={final_bin_path} -c {config_path}
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
"""
    
    install_service = ask_with_escape_back(
        questionary.confirm("Do you want to create a Systemd service?", default=True, style=style)
    )
    
    if install_service and install_service != BACK_VALUE:
        service_file_path = f"/etc/systemd/system/{service_name}.service"
        local_service_path = work_dir / f"{service_name}.service"
        
        with open(local_service_path, "w") as f:
            f.write(service_content)
            
        print("\nTo install the service, run the following commands:")
        print(f"sudo cp {local_service_path} {service_file_path}")
        print("sudo systemctl daemon-reload")
        print(f"sudo systemctl enable {service_name}")
        print(f"sudo systemctl start {service_name}")
        print(f"sudo systemctl status {service_name}")
        
        # Optional: Try to run with sudo if user wants?
        # For now, just printing instructions is safer and requested in prompt "use sudo if needed, or print instructions"
    else:
        print("\nYou can run FRP manually with:")
        print(f"{final_bin_path} -c {config_path}")
