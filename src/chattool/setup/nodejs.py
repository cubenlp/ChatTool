from collections import deque
from importlib import resources
import json
import shlex
import shutil
import subprocess
from pathlib import Path
import click

from chattool.interaction import (
    BACK_VALUE,
    abort_if_force_without_tty,
    ask_confirm,
    ask_text,
    resolve_interactive_mode,
)
from chattool.utils.custom_logger import setup_logger

BUNDLED_NVM_VERSION = "v0.40.3"
MIN_NODEJS_MAJOR = 20
NVM_INIT_BEGIN = "# >>> chattool nvm >>>"
NVM_INIT_END = "# <<< chattool nvm <<<"
logger = setup_logger("setup_nodejs")


def _configure_logger(log_level="INFO"):
    global logger
    logger = setup_logger("setup_nodejs", log_level=str(log_level).upper())
    return logger


def _run_bash(command):
    return subprocess.run(["bash", "-c", command], capture_output=True, text=True)


def _run_bash_with_output_tail(command, tail_lines=80):
    process = subprocess.Popen(
        ["bash", "-c", command],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    tail = deque(maxlen=tail_lines)
    assert process.stdout is not None
    for line in process.stdout:
        tail.append(line.rstrip("\n"))
    return subprocess.CompletedProcess(
        process.args,
        process.wait(),
        "\n".join(tail).strip(),
        "",
    )


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


def _parse_node_major(version_text):
    if not version_text:
        return None
    text = str(version_text).strip()
    if text.startswith("v"):
        text = text[1:]
    major = text.split(".", 1)[0]
    if not major.isdigit():
        return None
    return int(major)


def _build_runtime(node_bin, npm_bin, node_version, npm_version, source):
    return {
        "node_bin": node_bin,
        "npm_bin": npm_bin,
        "node_version": node_version,
        "npm_version": npm_version,
        "node_major": _parse_node_major(node_version),
        "source": source,
    }


def _detect_nodejs_runtime_from_path():
    node_bin = shutil.which("node")
    npm_bin = shutil.which("npm")
    node_version = _get_cmd_output(["node", "-v"]) if node_bin else ""
    npm_version = _get_cmd_output(["npm", "-v"]) if npm_bin else ""
    return _build_runtime(node_bin, npm_bin, node_version, npm_version, "path")


def _detect_nodejs_runtime_from_nvm():
    nvm_sh = Path.home() / ".nvm" / "nvm.sh"
    if not nvm_sh.exists():
        return _build_runtime("", "", "", "", "nvm")

    prefix = 'export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && '
    node_bin = _get_bash_output(prefix + "command -v node")
    npm_bin = _get_bash_output(prefix + "command -v npm")
    node_version = _get_bash_output(prefix + "node -v") if node_bin else ""
    npm_version = _get_bash_output(prefix + "npm -v") if npm_bin else ""
    return _build_runtime(node_bin, npm_bin, node_version, npm_version, "nvm")


def _runtime_score(runtime):
    score = 0
    if runtime.get("node_bin"):
        score += 1
    if runtime.get("npm_bin"):
        score += 1
    node_major = runtime.get("node_major")
    if node_major is not None:
        score += 2 + node_major
    return score


def _detect_nodejs_runtime():
    path_runtime = _detect_nodejs_runtime_from_path()
    nvm_runtime = _detect_nodejs_runtime_from_nvm()
    if _runtime_score(nvm_runtime) > _runtime_score(path_runtime):
        return nvm_runtime
    return path_runtime


def _nodejs_requirement_message(runtime, min_major):
    node_version = runtime.get("node_version") or "not found"
    npm_version = runtime.get("npm_version") or "not found"
    if not runtime.get("node_bin") or not runtime.get("npm_bin"):
        return (
            f"Node.js >= {min_major} and npm are required, but node/npm were not found."
        )
    node_major = runtime.get("node_major")
    if node_major is None:
        return f"Node.js >= {min_major} is required, but the current Node.js version could not be parsed: {node_version}"
    if node_major < min_major:
        return (
            f"Node.js >= {min_major} is required, but the current runtime is "
            f"{node_version} with npm {npm_version}."
        )
    return ""


def has_required_nodejs(min_major=MIN_NODEJS_MAJOR, runtime=None):
    runtime = runtime or _detect_nodejs_runtime()
    node_major = runtime.get("node_major")
    return bool(
        runtime.get("node_bin")
        and runtime.get("npm_bin")
        and node_major is not None
        and node_major >= min_major
    )


def ensure_nodejs_requirement(
    min_major=MIN_NODEJS_MAJOR, interactive=None, can_prompt=False, log_level="INFO"
):
    _configure_logger(log_level)
    runtime = _detect_nodejs_runtime()
    logger.info(f"Checking Node.js runtime requirement (>= {min_major})")
    if has_required_nodejs(min_major=min_major, runtime=runtime):
        return runtime

    message = _nodejs_requirement_message(runtime, min_major=min_major)
    logger.warning(message)

    if interactive is not False and can_prompt:
        install_now = ask_confirm(
            f"{message} Install or upgrade Node.js now via `chattool setup nodejs`?",
            default=True,
        )
        if install_now == BACK_VALUE:
            raise click.Abort()
        if install_now:
            setup_nodejs(interactive=True, log_level=log_level)
            runtime = _detect_nodejs_runtime()
            if has_required_nodejs(min_major=min_major, runtime=runtime):
                return runtime
            logger.error("Node.js requirement still not satisfied after setup")
            click.echo(
                f"Node.js >= {min_major} is still not available after setup. Please verify your shell environment.",
                err=True,
            )
            raise click.Abort()

    click.echo(message, err=True)
    click.echo("Please run: chattool setup nodejs", err=True)
    raise click.Abort()


def run_npm_command(args, cwd=None):
    quoted_args = " ".join(shlex.quote(str(arg)) for arg in args)
    click.echo(f"Running: npm {quoted_args}")
    runtime = _detect_nodejs_runtime()
    if runtime.get("source") == "nvm":
        cwd_prefix = (
            f"cd {shlex.quote(str(cwd))} && " if cwd is not None else ""
        )
        command = (
            'export NVM_DIR="$HOME/.nvm" && '
            '[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && '
            f"{cwd_prefix}"
            f"npm {quoted_args}"
        )
        return _run_bash(command)
    return subprocess.run(["npm", *args], capture_output=True, text=True, cwd=cwd)


def get_global_npm_package_version(package_name):
    result = run_npm_command(["list", "-g", package_name, "--depth=0", "--json"])
    if result.returncode != 0:
        return None
    try:
        payload = json.loads(result.stdout or "{}")
    except Exception:
        return None
    dependencies = payload.get("dependencies")
    if not isinstance(dependencies, dict):
        return None
    package = dependencies.get(package_name)
    if not isinstance(package, dict):
        return None
    version = package.get("version")
    if not isinstance(version, str) or not version.strip():
        return None
    return version.strip()


def should_install_global_npm_package(
    package_name, display_name, interactive=None, can_prompt=False, default_update=False
):
    version = get_global_npm_package_version(package_name)
    if not version:
        return True

    click.echo(f"{display_name} already installed: {version}")
    if interactive is not False and can_prompt:
        update_now = ask_confirm(
            f"Update {display_name} now via npm install -g?",
            default=default_update,
        )
        if update_now == BACK_VALUE:
            raise click.Abort()
        if update_now:
            return True
        click.echo(f"Skip updating {display_name}.")
        return False

    click.echo(f"Skip npm install for {display_name}. Use -i to confirm an update.")
    return False


def _replace_managed_block(path, begin_marker, end_marker, block):
    content = ""
    if path.exists():
        content = path.read_text(encoding="utf-8")

    begin_idx = content.find(begin_marker)
    end_idx = content.find(end_marker)
    if begin_idx != -1 and end_idx != -1 and end_idx >= begin_idx:
        end_idx += len(end_marker)
        if end_idx < len(content) and content[end_idx : end_idx + 1] == "\n":
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


def _read_bundled_nvm_script():
    return (
        resources.files("chattool.setup")
        .joinpath("assets/nvm.sh")
        .read_text(encoding="utf-8")
    )


def _render_nvm_init_block():
    lines = [
        NVM_INIT_BEGIN,
        'export NVM_DIR="$HOME/.nvm"',
        '[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"',
        NVM_INIT_END,
    ]
    return "\n".join(lines) + "\n"


def _resolve_shell_rc_targets(interactive=False):
    from chattool.setup.alias import (
        BACK_VALUE,
        resolve_shell_rc,
        resolve_target_shells,
        select_target_shells_interactively,
    )

    shell_names = resolve_target_shells(None)
    if interactive:
        shell_names = select_target_shells_interactively(shell_names)
        if shell_names == BACK_VALUE:
            raise click.Abort()

    if not shell_names:
        click.echo("No shells selected for nvm init update.", err=True)
        raise click.Abort()

    return [(shell_name, resolve_shell_rc(shell_name)) for shell_name in shell_names]


def _install_bundled_nvm(nvm_sh, shell_targets):
    logger.info(f"Writing bundled nvm.sh ({BUNDLED_NVM_VERSION}) to {nvm_sh}")
    nvm_sh.parent.mkdir(parents=True, exist_ok=True)
    nvm_sh.write_text(_read_bundled_nvm_script(), encoding="utf-8")
    nvm_sh.chmod(0o755)
    block = _render_nvm_init_block()
    for _, shell_rc in shell_targets:
        _replace_managed_block(shell_rc, NVM_INIT_BEGIN, NVM_INIT_END, block)


def _echo_recent_output(result, heading):
    output = (result.stdout or "").strip()
    if not output:
        return
    click.echo(heading, err=True)
    click.echo(output, err=True)


def setup_nodejs(interactive=None, log_level="INFO"):
    _configure_logger(log_level)
    logger.info("Start nodejs setup")
    usage = "Usage: chattool setup nodejs [-i|-I]"
    interactive, can_prompt, force_interactive, _, need_prompt = (
        resolve_interactive_mode(
            interactive=interactive,
            auto_prompt_condition=False,
        )
    )
    abort_if_force_without_tty(force_interactive, can_prompt, usage)

    runtime = _detect_nodejs_runtime()
    if has_required_nodejs() and not need_prompt:
        node_version = runtime["node_version"]
        npm_version = runtime["npm_version"]
        click.echo(f"Node.js already installed: {node_version}")
        click.echo(f"npm already installed: {npm_version}")
        click.echo("Use -i to install/switch version with nvm.")
        return
    if (
        runtime.get("node_bin")
        and runtime.get("npm_bin")
        and runtime.get("node_major") is not None
        and runtime["node_major"] < MIN_NODEJS_MAJOR
    ):
        click.echo(
            f"Detected Node.js {runtime['node_version']} with npm {runtime['npm_version']}. "
            f"Upgrading to Node.js >= {MIN_NODEJS_MAJOR} via nvm..."
        )

    nvm_sh = Path.home() / ".nvm" / "nvm.sh"
    shell_targets = _resolve_shell_rc_targets(interactive=need_prompt)
    if not nvm_sh.exists():
        logger.info(f"nvm not found, installing bundled nvm ({BUNDLED_NVM_VERSION})")
        click.echo(f"nvm not found, writing bundled nvm.sh ({BUNDLED_NVM_VERSION})...")
        try:
            _install_bundled_nvm(nvm_sh, shell_targets)
        except Exception as exc:
            logger.error(f"Failed to install bundled nvm: {exc}")
            click.echo("Failed to install bundled nvm.", err=True)
            raise click.Abort() from exc
        click.echo(f"Bundled nvm installed: {nvm_sh}")
        for shell_name, shell_rc in shell_targets:
            click.echo(f"Updated {shell_name} init: {shell_rc}")
    else:
        click.echo(f"Found nvm: {nvm_sh}")
        block = _render_nvm_init_block()
        for shell_name, shell_rc in shell_targets:
            _replace_managed_block(shell_rc, NVM_INIT_BEGIN, NVM_INIT_END, block)
            logger.info(f"Ensured nvm init block in {shell_rc}")
            click.echo(f"Ensured nvm init in {shell_rc} ({shell_name})")

    version_spec = "lts/*"
    if need_prompt:
        version_spec = ask_text("Node.js version to install via nvm", default="lts/*")

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
    result = _run_bash_with_output_tail(nvm_cmd)
    if result.returncode != 0:
        logger.error(
            f"Failed to install/use Node.js via nvm for version target: {version_spec}"
        )
        click.echo("Failed to install/use Node.js via nvm.", err=True)
        _echo_recent_output(result, "Recent nvm output:")
        raise click.Abort()

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
