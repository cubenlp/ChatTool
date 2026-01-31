import click
from chattool.client.ssl_updater import main as ssl_updater_main
from chattool.client.dns_updater import cli as dns_updater_cli
from chattool.fastobj.capture import main as capture_main
from chattool.client.env_manager import cli as env_cli

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

serve.add_command(capture_main, name='capture')

# Env Group
cli.add_command(env_cli, name='env')

def main():
    cli()

if __name__ == '__main__':
    main()
