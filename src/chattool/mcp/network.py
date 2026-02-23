from typing import List, Optional
try:
    from fastmcp import FastMCP
except ImportError:
    FastMCP = None
from chattool.tools.network.scanner import ping_scan, port_scan

def network_ping_scan(
    network_segment: str, 
    concurrency: int = 50
) -> List[str]:
    """
    Scan a network segment for active hosts using ICMP ping.
    
    Args:
        network_segment: Network segment to scan (e.g., 192.168.1.0/24).
        concurrency: Number of concurrent threads (default: 50).
        
    Returns:
        List of active IP addresses.
    """
    return ping_scan(network_segment, concurrency=concurrency)

def network_port_scan(
    hosts: List[str], 
    port: int = 22, 
    concurrency: int = 50
) -> List[str]:
    """
    Scan a list of hosts for a specific open port.
    
    Args:
        hosts: List of IP addresses to scan.
        port: Port number to check (default: 22).
        concurrency: Number of concurrent threads (default: 50).
        
    Returns:
        List of hosts with the port open.
    """
    return port_scan(hosts, port, concurrency=concurrency)

def register(mcp: FastMCP):
    """Register Network tools with the MCP server."""
    mcp.tool(name="network_ping_scan", tags=["network", "read"])(network_ping_scan)
    mcp.tool(name="network_port_scan", tags=["network", "read"])(network_port_scan)
