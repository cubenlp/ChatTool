import shlex
import shutil
import subprocess
from pathlib import Path
import click

from chattool.setup.interactive import abort_if_force_without_tty, resolve_interactive_mode
from chattool.utils.custom_logger import setup_logger

NVM_INSTALL_VERSION = "v0.40.3"
logger = setup_logger("setup_nodejs")

def _run_bash(command):
    return subprocess.run(["bash", "-lc", command], capture_output=True, text=True)

def _get_cmd_output(command):
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    return ""

def _get_bash_output(command):
    result = _run_bash(command)
    if result.returncode == 0:
        return result.stdout.strip()
    return ""

def setup_nodejs(interactive=None):
    logger.info("Start nodejs setup")
    usage = "Usage: chattool setup nodejs [-i|-I]"
    interactive, can_prompt, force_interactive, _, need_prompt = resolve_interactive_mode(
        interactive=interactive,
        auto_prompt_condition=False,
    )
    abort_if_force_without_tty(force_interactive, can_prompt, usage)

    node_bin = shutil.which("node")
    npm_bin = shutil.which("npm")
    if node_bin and npm_bin and not need_prompt:
        node_version = _get_cmd_output(["node", "-v"])
        npm_version = _get_cmd_output(["npm", "-v"])
        click.echo(f"Node.js already installed: {node_version}")
        click.echo(f"npm already installed: {npm_version}")
        click.echo("Use -i to install/switch version with nvm.")
        return

    nvm_sh = Path.home() / ".nvm" / "nvm.sh"
    if not nvm_sh.exists():
        logger.info("nvm not found, installing nvm")
        click.echo("nvm not found, installing nvm...")
        install_cmd = f"curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/{NVM_INSTALL_VERSION}/install.sh | bash"
        install_result = _run_bash(install_cmd)
        if install_result.returncode != 0:
            logger.error("Failed to install nvm")
            click.echo("Failed to install nvm.", err=True)
            if install_result.stderr:
                click.echo(install_result.stderr.strip(), err=True)
            raise click.Abort()
        click.echo("nvm installed.")
    else:
        click.echo(f"Found nvm: {nvm_sh}")

    version_spec = "lts/*"
    if need_prompt:
        version_spec = click.prompt("Node.js version to install via nvm", default="lts/*")

    quoted_version = shlex.quote(version_spec)
    click.echo(f"Installing Node.js via nvm ({version_spec})...")
    nvm_cmd = (
        'export NVM_DIR="$HOME/.nvm" && '
        '[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && '
        f"nvm install {quoted_version} && "
        f"nvm alias default {quoted_version} && "
        "nvm use default && "
        "node -v && npm -v"
    )
    result = _run_bash(nvm_cmd)
    if result.returncode != 0:
        logger.error(f"Failed to install/use Node.js via nvm for version target: {version_spec}")
        click.echo("Failed to install/use Node.js via nvm.", err=True)
        if result.stderr:
            click.echo(result.stderr.strip(), err=True)
        raise click.Abort()

    output = (result.stdout or "").strip()
    error_output = (result.stderr or "").strip()
    if output:
        click.echo(output)
    if error_output:
        click.echo(error_output)

    node_version = _get_bash_output(
        'export NVM_DIR="$HOME/.nvm" && '
        '[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && '
        "node -v"
    )
    npm_version = _get_bash_output(
        'export NVM_DIR="$HOME/.nvm" && '
        '[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && '
        "npm -v"
    )
    if node_version:
        click.echo(f"Node.js version: {node_version}")
    if npm_version:
        click.echo(f"npm version: {npm_version}")
    if not node_version or not npm_version:
        click.echo("Node.js was installed but may not be available in current shell.")
        click.echo("Open a new terminal or run: source ~/.nvm/nvm.sh")

    logger.info(f"Node.js setup completed with version target: {version_spec}")
    click.echo(f"Node.js setup completed with version target: {version_spec}")
