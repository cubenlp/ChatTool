import click
import json
from chattool.tools import TPLogin

@click.group()
def cli():
    """TP-Link Router Tool"""
    pass

@cli.command()
def info():
    """Get device info"""
    try:
        client = TPLogin()
        info = client.get_device_info()
        if info:
            click.echo(json.dumps(info, indent=2, ensure_ascii=False))
        else:
            click.echo("Failed to get device info", err=True)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@cli.command()
def virtual_servers():
    """Get virtual servers"""
    try:
        client = TPLogin()
        servers = client.get_virtual_servers()
        if servers:
            click.echo(json.dumps(servers, indent=2, ensure_ascii=False))
        else:
            click.echo("No virtual servers found or failed to fetch", err=True)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
