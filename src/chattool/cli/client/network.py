import click
import os
import ipaddress
from chattool.tools.network.scanner import ping_scan, port_scan

@click.group()
def network():
    """Network scanning tools."""
    pass

@network.command()
@click.option('-net', '--network', required=True, help='Network segment to scan (e.g. 192.168.1.0/24)')
@click.option('-n', '--concurrency', default=50, help='Number of concurrent threads')
@click.option('-o', '--output', default=None, help='Output file path')
def ping(network, concurrency, output):
    """Scan a network for active hosts using ICMP ping."""
    ping_scan(network_segment=network, concurrency=concurrency, output_path=output)

@network.command()
@click.option('-i', '--input', required=False, help='Input file containing list of IPs')
@click.option('-net', '--network', required=False, help='Network segment to scan (e.g. 192.168.1.0/24)')
@click.option('-p', '--port', default=22, help='Port to scan (default: 22 for SSH)')
@click.option('-n', '--concurrency', default=50, help='Number of concurrent threads')
@click.option('-o', '--output', default=None, help='Output file path')
def ssh(input, network, port, concurrency, output):
    """Scan IPs for open SSH ports."""
    ip_list = []
    
    if input:
        if not os.path.exists(input):
            click.echo(f"Error: Input file '{input}' not found.")
            return
        with open(input, 'r') as f:
            ip_list = [line.strip() for line in f if line.strip()]
    elif network:
        try:
            net = ipaddress.ip_network(network, strict=False)
            ip_list = [str(ip) for ip in net.hosts()]
        except ValueError as e:
            click.echo(f"Error parsing network: {e}")
            return
    else:
        click.echo("Error: Either --input or --network must be provided.")
        return

    port_scan(ip_list=ip_list, port=port, concurrency=concurrency, output_path=output)

if __name__ == '__main__':
    network()
