import click
from chattool.client.ssl_updater import main as ssl_updater_main
from chattool.client.dns_updater import cli as dns_updater_cli
from chattool.fastobj.capture import main as capture_main

@click.group()
def cli():
    """ChatTool CLI - Unified entry point for ChatTool services and scripts."""
    pass

@cli.group()
def script():
    """One-off scripts and utilities."""
    pass

@cli.group()
def service():
    """Long-running services and daemons."""
    pass

# Register commands
script.add_command(ssl_updater_main, name='cert-updater')
service.add_command(dns_updater_cli, name='dns-updater')
service.add_command(capture_main, name='capture')

def main():
    cli()

if __name__ == '__main__':
    main()
