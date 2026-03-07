import click
from chattool.setup.chrome import setup_chrome_driver
from chattool.setup.frp import setup_frp

@click.group(name="setup")
def setup_group():
    """Setup tools for ChatTool."""
    pass

@setup_group.command(name="chrome")
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode to choose install directory.')
def chrome_cmd(interactive):
    """Setup Chrome and Chromedriver."""
    setup_chrome_driver(interactive=interactive)

@setup_group.command(name="frp")
def frp_cmd():
    """Setup FRP Client/Server."""
    setup_frp()
