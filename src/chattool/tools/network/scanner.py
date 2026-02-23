import concurrent.futures
import subprocess
import socket
import platform
import ipaddress
import threading
from typing import List, Tuple, Union

def get_platform_ping_args(count: int = 1, timeout: int = 1) -> List[str]:
    """
    Returns platform-specific ping arguments.
    """
    system = platform.system().lower()
    args = ['ping']
    
    if system == 'windows':
        args.extend(['-n', str(count)])
        args.extend(['-w', str(timeout * 1000)]) # ms
    elif system == 'darwin':
        args.extend(['-c', str(count)])
        args.extend(['-W', str(timeout * 1000)]) # ms for macOS
    else: # Linux and others
        args.extend(['-c', str(count)])
        args.extend(['-W', str(timeout)]) # seconds for Linux
        
    return args

def ping_host(host: str, timeout: int = 1) -> Tuple[str, bool]:
    """
    Pings a single host to check if it's active.
    Returns (host, is_active).
    """
    command = get_platform_ping_args(count=1, timeout=timeout)
    command.append(host)
    
    try:
        subprocess.run(
            command, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL, 
            check=True
        )
        return host, True
    except subprocess.CalledProcessError:
        return host, False

def check_port(host: str, port: int, timeout: float = 1.0) -> Tuple[str, bool]:
    """
    Checks if a single port is open on a host.
    Returns (host, is_open).
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return host, True
    except (socket.timeout, socket.error):
        return host, False

def ping_scan(network_segment: str, concurrency: int = 50, output_path: str = None) -> List[str]:
    """
    Scans a network segment for active hosts.
    """
    try:
        network = ipaddress.ip_network(network_segment, strict=False)
        hosts = [str(ip) for ip in network.hosts()]
    except ValueError as e:
        print(f"Error parsing network segment: {e}")
        return []

    if output_path:
        # Clear the file first
        with open(output_path, 'w') as f:
            pass

    active_hosts = []
    print(f"Scanning {len(hosts)} hosts in {network_segment} with {concurrency} threads...")
    
    # Lock for file writing
    write_lock = threading.Lock()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_to_host = {executor.submit(ping_host, host): host for host in hosts}
        for future in concurrent.futures.as_completed(future_to_host):
            host, is_active = future.result()
            if is_active:
                print(f"Active: {host}")
                active_hosts.append(host)
                if output_path:
                    with write_lock:
                        with open(output_path, 'a') as f:
                            f.write(f"{host}\n")
                            f.flush()
    
    active_hosts.sort(key=lambda ip: ipaddress.ip_address(ip))
    
    if output_path:
        print(f"Results saved to {output_path}")
        
    return active_hosts

def port_scan(ip_list: List[str], port: int, concurrency: int = 50, output_path: str = None) -> List[str]:
    """
    Scans a specific port on a list of IPs.
    """
    if output_path:
        # Clear the file first
        with open(output_path, 'w') as f:
            pass

    open_hosts = []
    print(f"Scanning port {port} on {len(ip_list)} hosts with {concurrency} threads...")
    
    # Lock for file writing
    write_lock = threading.Lock()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_to_host = {executor.submit(check_port, ip, port): ip for ip in ip_list}
        for future in concurrent.futures.as_completed(future_to_host):
            host, is_open = future.result()
            if is_open:
                print(f"Open: {host}:{port}")
                open_hosts.append(host)
                if output_path:
                    with write_lock:
                        with open(output_path, 'a') as f:
                            f.write(f"{host}\n")
                            f.flush()
                
    open_hosts.sort(key=lambda ip: ipaddress.ip_address(ip))
    
    if output_path:
        print(f"Results saved to {output_path}")
        
    return open_hosts
