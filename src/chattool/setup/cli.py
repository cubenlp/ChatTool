import click
from chattool.setup.chrome import setup_chrome_driver
from chattool.setup.frp import setup_frp
from chattool.setup.nodejs import setup_nodejs
from chattool.setup.codex import setup_codex

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

@setup_group.command(name="nodejs")
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode to choose Node.js version.')
def nodejs_cmd(interactive):
    """Setup nvm and Node.js (default LTS)."""
    setup_nodejs(interactive=interactive)

@setup_group.command(name="codex")
@click.option('--preferred-auth-method', '--pam', default=None, help='Value for preferred_auth_method and OPENAI_API_KEY.')
def codex_cmd(preferred_auth_method):
    """Setup Codex CLI and config files."""
    setup_codex(preferred_auth_method=preferred_auth_method)
