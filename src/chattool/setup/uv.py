import os
import shlex
import shutil
import site
import subprocess
import sys
from pathlib import Path

import click

from chattool.setup.alias import resolve_shell, resolve_shell_rc
from chattool.setup.interactive import abort_if_force_without_tty, resolve_interactive_mode
from chattool.utils.custom_logger import setup_logger
from chattool.utils.tui import BACK_VALUE, ask_confirm, ask_text

try:
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


DEFAULT_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple/"
UV_CONFIG_BEGIN = "# >>> chattool uv >>>"
UV_CONFIG_END = "# <<< chattool uv <<<"
UV_ACTIVATE_BEGIN = "# >>> chattool uv activate >>>"
UV_ACTIVATE_END = "# <<< chattool uv activate <<<"
logger = setup_logger("setup_uv")


def _normalize_path(value) -> Path:
    if isinstance(value, Path):
        return value.expanduser().resolve()
    if value is None:
        return Path.cwd().resolve()
    text = str(value).strip()
    if not text:
        return Path.cwd().resolve()
    return Path(text).expanduser().resolve()


def _replace_managed_block(path: Path, begin_marker: str, end_marker: str, block: str) -> None:
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


def _render_uv_index_block(default_index: str) -> str:
    return (
        f"{UV_CONFIG_BEGIN}\n"
        "[[index]]\n"
        'name = "chattool"\n'
        f'url = "{default_index}"\n'
        "default = true\n"
        f"{UV_CONFIG_END}\n"
    )


def _render_activation_block(project_dir: Path) -> str:
    activate_path = project_dir / ".venv" / "bin" / "activate"
    quoted_path = shlex.quote(str(activate_path))
    return (
        f"{UV_ACTIVATE_BEGIN}\n"
        f"source {quoted_path}\n"
        f"{UV_ACTIVATE_END}\n"
    )


def _load_pyproject(project_dir: Path) -> dict:
    pyproject_path = project_dir / "pyproject.toml"
    if not pyproject_path.exists():
        raise click.ClickException(f"未找到 pyproject.toml: {pyproject_path}")
    return tomllib.loads(pyproject_path.read_text(encoding="utf-8"))


def _read_existing_python_version(project_dir: Path) -> str | None:
    version_path = project_dir / ".python-version"
    if not version_path.exists():
        return None
    value = version_path.read_text(encoding="utf-8").strip()
    return value or None


def _read_existing_default_index(uv_config_path: Path) -> str | None:
    if not uv_config_path.exists():
        return None
    try:
        data = tomllib.loads(uv_config_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    indexes = data.get("index")
    if not isinstance(indexes, list):
        return None
    for entry in indexes:
        if not isinstance(entry, dict):
            continue
        if entry.get("default") is True and isinstance(entry.get("url"), str):
            url = entry["url"].strip()
            if url:
                return url
    return None


def _infer_python_version(project_dir: Path, pyproject_data: dict) -> str:
    existing = _read_existing_python_version(project_dir)
    if existing:
        return existing

    classifiers = pyproject_data.get("project", {}).get("classifiers", [])
    versions = []
    if isinstance(classifiers, list):
        prefix = "Programming Language :: Python :: "
        for item in classifiers:
            if not isinstance(item, str) or not item.startswith(prefix):
                continue
            value = item[len(prefix):].strip()
            parts = value.split(".")
            if len(parts) != 2 or not all(part.isdigit() for part in parts):
                continue
            versions.append((int(parts[0]), int(parts[1])))
    if versions:
        highest = max(versions)
        return f"{highest[0]}.{highest[1]}"

    return f"{sys.version_info.major}.{sys.version_info.minor}"


def _project_has_dev_extra(pyproject_data: dict) -> bool:
    optional = pyproject_data.get("project", {}).get("optional-dependencies", {})
    return isinstance(optional, dict) and "dev" in optional


def _uv_user_bin_candidates() -> list[Path]:
    user_base = Path(site.getuserbase())
    candidates = [user_base / "bin" / "uv", user_base / "Scripts" / "uv.exe"]
    return [candidate for candidate in candidates if candidate.exists()]


def detect_uv_binary() -> str | None:
    system_uv = shutil.which("uv")
    if system_uv:
        return system_uv
    for candidate in _uv_user_bin_candidates():
        return str(candidate)
    return None


def _run_command(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )


def _ensure_uv_available(interactive, can_prompt) -> str:
    uv_bin = detect_uv_binary()
    if uv_bin:
        logger.info(f"Found uv binary: {uv_bin}")
        return uv_bin

    if interactive is not False and can_prompt:
        install_now = ask_confirm(
            "uv 未安装。现在通过 `python -m pip install --user -U uv` 安装吗？",
            default=True,
        )
        if install_now == BACK_VALUE:
            raise click.Abort()
        if not install_now:
            click.echo("已取消 uv 安装。", err=True)
            raise click.Abort()

    logger.info("Installing uv with pip --user")
    result = _run_command([sys.executable, "-m", "pip", "install", "--user", "-U", "uv"])
    if result.returncode != 0:
        logger.error("Failed to install uv")
        click.echo("Failed to install uv.", err=True)
        stderr = (result.stderr or "").strip()
        if stderr:
            click.echo(stderr, err=True)
        raise click.Abort()

    uv_bin = detect_uv_binary()
    if not uv_bin:
        click.echo("uv installed, but executable was not found in expected user scripts path.", err=True)
        raise click.Abort()

    click.echo(f"Installed uv: {uv_bin}")
    return uv_bin


def _configure_uv_index(default_index: str) -> Path:
    uv_config_path = Path.home() / ".config" / "uv" / "uv.toml"
    _replace_managed_block(
        uv_config_path,
        UV_CONFIG_BEGIN,
        UV_CONFIG_END,
        _render_uv_index_block(default_index),
    )
    return uv_config_path


def _configure_shell_activation(project_dir: Path) -> Path:
    if os.name != "posix":
        raise click.ClickException("uv shell activation currently only supports Unix-like shells.")
    shell_name = resolve_shell(None)
    rc_path = resolve_shell_rc(shell_name)
    _replace_managed_block(
        rc_path,
        UV_ACTIVATE_BEGIN,
        UV_ACTIVATE_END,
        _render_activation_block(project_dir),
    )
    return rc_path


def _sync_command_args(include_dev: bool, has_dev_extra: bool) -> list[str]:
    args = ["sync"]
    if include_dev and has_dev_extra:
        args.extend(["--extra", "dev"])
    return args


def _run_uv_or_abort(uv_bin: str, project_dir: Path, args: list[str], label: str) -> None:
    result = _run_command([uv_bin, *args], cwd=project_dir)
    if result.returncode != 0:
        logger.error(f"uv {label} failed in {project_dir}")
        click.echo(f"Failed to run uv {label}.", err=True)
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        if stderr:
            click.echo(stderr, err=True)
        elif stdout:
            click.echo(stdout, err=True)
        raise click.Abort()


def setup_uv(
    project_dir=None,
    python_version=None,
    default_index=None,
    activate_shell=None,
    include_dev=None,
    interactive=None,
):
    logger.info("Start uv setup")
    project_path = _normalize_path(project_dir)
    pyproject_data = _load_pyproject(project_path)
    has_dev_extra = _project_has_dev_extra(pyproject_data)
    uv_config_path = Path.home() / ".config" / "uv" / "uv.toml"
    existing_default_index = _read_existing_default_index(uv_config_path)
    inferred_python = _infer_python_version(project_path, pyproject_data)
    usage = (
        "Usage: chattool setup uv [--project-dir <path>] [--python <version>] "
        "[--default-index <url>] [--activate-shell/--no-activate-shell] "
        "[--include-dev/--no-include-dev] [-i|-I]"
    )

    interactive, can_prompt, force_interactive, _, need_prompt = resolve_interactive_mode(
        interactive=interactive,
        auto_prompt_condition=(
            python_version is None
            or activate_shell is None
            or include_dev is None
            or default_index is None
        ),
    )
    abort_if_force_without_tty(force_interactive, can_prompt, usage)

    if need_prompt:
        project_input = ask_text("project_dir", default=str(project_path))
        if project_input == BACK_VALUE:
            return
        project_path = _normalize_path(project_input)
        pyproject_data = _load_pyproject(project_path)
        has_dev_extra = _project_has_dev_extra(pyproject_data)
        inferred_python = _infer_python_version(project_path, pyproject_data)

        python_value = ask_text("python version", default=python_version or inferred_python)
        if python_value == BACK_VALUE:
            return
        python_version = python_value

        existing_index_default = default_index if default_index is not None else (existing_default_index or "")
        default_index_value = ask_text("default_index (optional)", default=existing_index_default)
        if default_index_value == BACK_VALUE:
            return
        default_index = default_index_value.strip()

        if include_dev is None and has_dev_extra:
            include_dev_choice = ask_confirm(
                "项目检测到 `dev` extra，是否执行 `uv sync --extra dev`？",
                default=True,
            )
            if include_dev_choice == BACK_VALUE:
                return
            include_dev = bool(include_dev_choice)
        elif include_dev is None:
            include_dev = False

        if activate_shell is None:
            activate_choice = ask_confirm(
                "是否将当前项目的 `.venv` 激活脚本追加到 shell rc（.zshrc/.bashrc）？",
                default=False,
            )
            if activate_choice == BACK_VALUE:
                return
            activate_shell = bool(activate_choice)

    python_version = (python_version or inferred_python).strip()
    default_index = (default_index or "").strip()
    include_dev = has_dev_extra if include_dev is None else bool(include_dev)
    activate_shell = False if activate_shell is None else bool(activate_shell)

    if not python_version:
        click.echo("Missing python version.", err=True)
        raise click.Abort()

    uv_bin = _ensure_uv_available(interactive=interactive, can_prompt=can_prompt)

    if default_index:
        config_path = _configure_uv_index(default_index)
        click.echo(f"Updated uv config: {config_path}")
    elif existing_default_index:
        click.echo(f"Keep existing uv default index: {existing_default_index}")

    _run_uv_or_abort(uv_bin, project_path, ["python", "pin", python_version], "python pin")
    _run_uv_or_abort(uv_bin, project_path, ["lock"], "lock")
    sync_args = _sync_command_args(include_dev=include_dev, has_dev_extra=has_dev_extra)
    _run_uv_or_abort(uv_bin, project_path, sync_args, "sync")

    if activate_shell:
        rc_path = _configure_shell_activation(project_path)
        click.echo(f"Updated shell activation: {rc_path}")
        click.echo(f"Run: source {rc_path}")

    click.echo("uv setup completed.")
    click.echo(f"Project: {project_path}")
    click.echo(f"Python: {python_version}")
    click.echo(f"Sync command: uv {' '.join(sync_args)}")
    if default_index:
        click.echo(f"Default index: {default_index}")
