from importlib import resources
import shlex
import shutil
import subprocess
from pathlib import Path
import click

from chattool.setup.interactive import abort_if_force_without_tty, resolve_interactive_mode
from chattool.utils.custom_logger import setup_logger

BUNDLED_NVM_VERSION = "v0.40.3"
NVM_INIT_BEGIN = "# >>> chattool nvm >>>"
NVM_INIT_END = "# <<< chattool nvm <<<"
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


def _read_bundled_nvm_script():
    return resources.files("chattool.setup").joinpath("assets/nvm.sh").read_text(encoding="utf-8")


def _render_nvm_init_block():
    lines = [
        NVM_INIT_BEGIN,
        'export NVM_DIR="$HOME/.nvm"',
        '[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"',
        NVM_INIT_END,
    ]
    return "\n".join(lines) + "\n"


def _replace_managed_block(path, begin_marker, end_marker, block):
    content = ""
    if path.exists():
        content = path.read_text(encoding="utf-8")

    begin_idx = content.find(begin_marker)
    end_idx = content.find(end_marker)
    if begin_idx != -1 and end_idx != -1 and end_idx >= begin_idx:
        end_idx += len(end_marker)
        if end_idx < len(content) and content[end_idx:end_idx + 1] == "\n":
            end_idx += 1
        content = content[:begin_idx] + content[end_idx:]

    content = content.rstrip("\n")
    if block:
        if content:
            content = content + "\n\n" + block.rstrip("\n")
        else:
            content = block.rstrip("\n")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content + ("\n" if content else ""), encoding="utf-8")


def _resolve_shell_rc_path():
    from chattool.setup.alias import resolve_shell, resolve_shell_rc

    shell_name = resolve_shell(None)
    return resolve_shell_rc(shell_name), shell_name


def _install_bundled_nvm(nvm_sh, shell_rc):
    logger.info(f"Writing bundled nvm.sh ({BUNDLED_NVM_VERSION}) to {nvm_sh}")
    nvm_sh.parent.mkdir(parents=True, exist_ok=True)
    nvm_sh.write_text(_read_bundled_nvm_script(), encoding="utf-8")
    nvm_sh.chmod(0o755)
    _replace_managed_block(shell_rc, NVM_INIT_BEGIN, NVM_INIT_END, _render_nvm_init_block())


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
    shell_rc, shell_name = _resolve_shell_rc_path()
    if not nvm_sh.exists():
        logger.info(f"nvm not found, installing bundled nvm ({BUNDLED_NVM_VERSION})")
        click.echo(f"nvm not found, writing bundled nvm.sh ({BUNDLED_NVM_VERSION})...")
        try:
            _install_bundled_nvm(nvm_sh, shell_rc)
        except Exception as exc:
            logger.error(f"Failed to install bundled nvm: {exc}")
            click.echo("Failed to install bundled nvm.", err=True)
            raise click.Abort() from exc
        click.echo(f"Bundled nvm installed: {nvm_sh}")
        click.echo(f"Updated {shell_name} init: {shell_rc}")
    else:
        click.echo(f"Found nvm: {nvm_sh}")
        _replace_managed_block(shell_rc, NVM_INIT_BEGIN, NVM_INIT_END, _render_nvm_init_block())
        logger.info(f"Ensured nvm init block in {shell_rc}")
        click.echo(f"Ensured nvm init in {shell_rc}")

    version_spec = "lts/*"
    if need_prompt:
        version_spec = click.prompt("Node.js version to install via nvm", default="lts/*")

    quoted_version = shlex.quote(version_spec)
    logger.info(f"Running nvm install for version target: {version_spec}")
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
