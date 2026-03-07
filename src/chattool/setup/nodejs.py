import shlex
import shutil
import subprocess
from pathlib import Path
import click

NVM_INSTALL_VERSION = "v0.40.3"

def _run_bash(command):
    return subprocess.run(["bash", "-lc", command], capture_output=True, text=True)

def _get_cmd_output(command):
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    return ""

def setup_nodejs(interactive=False):
    node_bin = shutil.which("node")
    npm_bin = shutil.which("npm")
    if node_bin and npm_bin and not interactive:
        node_version = _get_cmd_output(["node", "-v"])
        npm_version = _get_cmd_output(["npm", "-v"])
        click.echo(f"Node.js already installed: {node_version}")
        click.echo(f"npm already installed: {npm_version}")
        click.echo("Use -i to install/switch version with nvm.")
        return

    nvm_sh = Path.home() / ".nvm" / "nvm.sh"
    if not nvm_sh.exists():
        click.echo("nvm not found, installing nvm...")
        install_cmd = f"curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/{NVM_INSTALL_VERSION}/install.sh | bash"
        install_result = _run_bash(install_cmd)
        if install_result.returncode != 0:
            click.echo("Failed to install nvm.", err=True)
            if install_result.stderr:
                click.echo(install_result.stderr.strip(), err=True)
            raise click.Abort()
        click.echo("nvm installed.")
    else:
        click.echo(f"Found nvm: {nvm_sh}")

    version_spec = "lts/*"
    if interactive:
        version_spec = click.prompt("Node.js version to install via nvm", default="lts/*")

    quoted_version = shlex.quote(version_spec)
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
        click.echo("Failed to install/use Node.js via nvm.", err=True)
        if result.stderr:
            click.echo(result.stderr.strip(), err=True)
        raise click.Abort()

    output = (result.stdout or "").strip()
    if output:
        click.echo(output)
    click.echo(f"Node.js setup completed with version target: {version_spec}")
