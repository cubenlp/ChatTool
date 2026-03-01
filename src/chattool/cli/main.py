import click
from .client import ssl_updater_main, dns_updater_cli, mcp_cli, cert_client, network_cli, lark_cli, image_cli
from .service import capture_app, cert_app, lark_serve_cli
from chattool.application.kb.cli import cli as kb_cli

@click.group()
def cli():
    """ChatTool CLI - Unified entry point for ChatTool services and scripts."""
    pass

# DNS Group
# dns_updater_cli is already a group containing 'list' and 'ddns'
cli.add_command(dns_updater_cli, name='dns')

# Add SSL cert updater to DNS group
dns_updater_cli.add_command(ssl_updater_main, name='cert-update')

# Serve Group
@cli.group()
def serve():
    """Local server tools."""
    pass

serve.add_command(capture_app, name='capture')
serve.add_command(cert_app, name='cert')
serve.add_command(lark_serve_cli, name='lark')

# Client Group
@cli.group()
def client():
    """Remote client tools."""
    pass

client.add_command(cert_client, name='cert')
client.add_command(image_cli, name='image')

# Network Group
cli.add_command(network_cli, name='network')

# MCP Group
cli.add_command(mcp_cli, name='mcp')

# KB Group
cli.add_command(kb_cli, name='kb')

# Lark Group
cli.add_command(lark_cli, name='lark')

# Image Group
# cli.add_command(image_cli, name='image')

def main():
    cli()

if __name__ == '__main__':
    main()
