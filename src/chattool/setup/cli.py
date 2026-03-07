import click
from chattool.setup.chrome import setup_chrome_driver
from chattool.setup.frp import setup_frp

@click.group(name="setup")
def setup_group():
    """Setup tools for ChatTool."""
    pass

@setup_group.command(name="chrome")
def chrome_cmd():
    """Setup Chrome and Chromedriver."""
    setup_chrome_driver()

@setup_group.command(name="frp")
def frp_cmd():
    """Setup FRP Client/Server."""
    setup_frp()
