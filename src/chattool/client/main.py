import click
from chattool.client.cert_updater import main as ssl_updater_main
from chattool.client.dns_updater import cli as dns_updater_cli
from chattool.client.service import capture_app, cert_app
from chattool.client.env_manager import cli as env_cli
from chattool.client.mcp import cli as mcp_cli
from chattool.application.kb.cli import cli as kb_cli
from chattool.client.cert_client import cert_client

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

# Client Group
@cli.group()
def client():
    """Remote client tools."""
    pass

client.add_command(cert_client, name='cert')

# Env Group
cli.add_command(env_cli, name='env')

# MCP Group
cli.add_command(mcp_cli, name='mcp')

# KB Group
cli.add_command(kb_cli, name='kb')

def main():
    cli()

if __name__ == '__main__':
    main()
