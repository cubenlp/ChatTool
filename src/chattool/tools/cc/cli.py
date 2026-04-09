"""
chattool cc - cc-connect 管理工具

提供最小可用的 cc-connect 安装、配置、启动与诊断能力。
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import time
from typing import Iterable

import click

from chattool.interaction import ask_confirm, ask_text


DEFAULT_CONFIG_DIR = Path.home() / ".cc-connect"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.toml"
DEFAULT_LOG_FILE = DEFAULT_CONFIG_DIR / "cc-connect.log"
DEFAULT_MAX_FAILURES = 5
DEFAULT_RETRY_DELAY = 2.0

AGENT_CHOICES = [
    "claudecode",
    "codex",
    "cursor",
    "gemini",
    "qoder",
    "opencode",
    "iflow",
]

PLATFORM_CHOICES = [
    "feishu",
    "dingtalk",
    "telegram",
    "slack",
    "discord",
    "wecom",
    "qq",
    "qqbot",
    "line",
]

AGENT_MODE_CHOICES: dict[str, list[str]] = {
    "codex": ["suggest", "auto-edit", "full-auto", "yolo"],
    "claudecode": ["default", "acceptEdits", "plan", "bypassPermissions", "dontAsk"],
    "cursor": ["default", "force", "plan", "ask"],
    "gemini": ["default", "auto-edit", "plan", "yolo"],
    "qoder": ["default", "yolo"],
    "opencode": ["default", "yolo"],
    "iflow": ["default", "auto-edit", "plan", "yolo"],
}

AGENT_MODE_DEFAULTS: dict[str, str] = {
    "codex": "suggest",
    "claudecode": "default",
    "cursor": "default",
    "gemini": "default",
    "qoder": "default",
    "opencode": "default",
    "iflow": "default",
}


@click.group(name="cc")
def cli() -> None:
    """管理 cc-connect (Remote AI Agent Bridge)."""
    pass


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(token in lowered for token in ("token", "secret", "key", "password"))


def _mask_value(value: str) -> str:
    if not value:
        return value
    if len(value) <= 4:
        return "****"
    return "*" * (len(value) - 4) + value[-4:]


def _toml_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _load_existing_defaults(config_path: Path) -> dict[str, object]:
    if not config_path.exists():
        return {}
    try:
        import tomllib  # Python 3.11+
    except ModuleNotFoundError:  # pragma: no cover
        try:
            import tomli as tomllib  # type: ignore
        except ModuleNotFoundError:
            return {}

    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

    projects = data.get("projects")
    if not projects or not isinstance(projects, list):
        return {}
    project = projects[0] or {}
    if not isinstance(project, dict):
        return {}

    agent = project.get("agent", {}) if isinstance(project.get("agent"), dict) else {}
    agent_opts = (
        agent.get("options", {}) if isinstance(agent.get("options"), dict) else {}
    )

    platforms = project.get("platforms")
    platform = platforms[0] if isinstance(platforms, list) and platforms else {}
    platform_type = None
    platform_opts = {}
    if isinstance(platform, dict):
        platform_type = platform.get("type")
        if isinstance(platform.get("options"), dict):
            platform_opts = platform.get("options") or {}

    return {
        "project": project.get("name"),
        "quiet": project.get("quiet"),
        "agent": agent.get("type"),
        "work_dir": agent_opts.get("work_dir"),
        "mode": agent_opts.get("mode"),
        "platform": platform_type,
        "platform_options": platform_opts,
    }


def _write_config(
    config_path: Path,
    project_name: str,
    quiet: bool | None,
    agent: str,
    work_dir: str,
    mode: str,
    platform: str,
    platform_options: dict[str, str] | None,
) -> None:
    platform_options = platform_options or {}
    lines: list[str] = []
    lines.append("[[projects]]")
    lines.append(f'name = "{_toml_string(project_name)}"')
    if quiet is not None:
        lines.append(f"quiet = {'true' if quiet else 'false'}")
    lines.append("")
    lines.append("[projects.agent]")
    lines.append(f'type = "{_toml_string(agent)}"')
    lines.append("")
    lines.append("[projects.agent.options]")
    lines.append(f'work_dir = "{_toml_string(work_dir)}"')
    lines.append(f'mode = "{_toml_string(mode)}"')
    lines.append("")
    lines.append("[[projects.platforms]]")
    lines.append(f'type = "{_toml_string(platform)}"')
    lines.append("")
    lines.append("[projects.platforms.options]")
    if platform_options:
        for key, value in platform_options.items():
            lines.append(f'{key} = "{_toml_string(value)}"')
    else:
        lines.append("# TODO: fill platform credentials here")
    if "proxy" not in platform_options:
        lines.append(
            '# proxy = ""  # optional: forward proxy for API calls if your IP is dynamic'
        )
        lines.append("#             # 可选：正向代理，用于 IP 不固定的场景")
        lines.append(
            '#             # e.g. "http://your-vps-ip:8888" — the VPS IP goes into trusted IP list'
        )
        lines.append(
            '#             # 示例："http://你的VPS-IP:8888" — 将 VPS IP 加入可信 IP 列表'
        )
        lines.append(
            '# proxy_username = ""  # optional: proxy authentication username / 代理认证用户名'
        )
        lines.append(
            '# proxy_password = ""  # optional: proxy authentication password / 代理认证密码'
        )
    lines.append("")

    _ensure_parent(config_path)
    config_path.write_text("\n".join(lines), encoding="utf-8")


def _prompt_platform_options() -> dict[str, str]:
    options: dict[str, str] = {}
    click.echo("输入平台配置项，按提示输入 key 与 value，直接回车结束")
    while True:
        key = ask_text("Option key", default="")
        if not key:
            break
        if _is_sensitive_key(key):
            value = ask_text(f"{key}", password=True)
        else:
            value = ask_text(f"{key}")
        options[key] = value
    return options


def _prompt_choice_text(
    label: str, choices: list[str], default: str | None = None
) -> str:
    prompt = label
    if default:
        prompt += f" ({'/'.join(choices)})"
    value = ask_text(prompt, default=default or "")
    normalized = str(value).strip()
    if normalized in choices:
        return normalized
    raise click.ClickException(f"{label} must be one of: {', '.join(choices)}")


def _prompt_secret_with_optional_default(label: str, default: str = "") -> str:
    if default:
        masked_default = _mask_value(default)
        entered = ask_text(f"{label} [{masked_default}]", default="", password=True)
        return entered or default
    return ask_text(label, default="", password=True)


def _get_feishu_candidate_options() -> dict[str, str]:
    from chattool.config import FeishuConfig

    candidates: dict[str, str] = {}
    if FeishuConfig.FEISHU_APP_ID.value:
        candidates["app_id"] = str(FeishuConfig.FEISHU_APP_ID.value)
    if FeishuConfig.FEISHU_APP_SECRET.value:
        candidates["app_secret"] = str(FeishuConfig.FEISHU_APP_SECRET.value)
    return candidates


def _prompt_platform_credentials(
    platform: str, existing: dict[str, str] | None
) -> dict[str, str]:
    existing = existing or {}
    if platform == "feishu":
        prompt_defaults = dict(_get_feishu_candidate_options())
        prompt_defaults.update(existing)
        if prompt_defaults and prompt_defaults != existing:
            masked = {
                key: (_mask_value(value) if _is_sensitive_key(key) else value)
                for key, value in prompt_defaults.items()
            }
            click.echo(f"检测到 chatenv 飞书配置候选: {masked}")

        app_id_default = prompt_defaults.get("app_id") or ""
        app_id = ask_text("app_id", default=app_id_default)
        app_secret_default = prompt_defaults.get("app_secret") or ""
        app_secret = _prompt_secret_with_optional_default(
            "app_secret", app_secret_default
        )
        return {"app_id": app_id, "app_secret": app_secret}
    if platform == "telegram":
        token_default = existing.get("token") or ""
        token = _prompt_secret_with_optional_default("token", token_default)
        return {"token": token}
    return _prompt_platform_options()


def _mask_proxy_options(options: dict[str, str]) -> dict[str, str]:
    masked = {}
    for key in ("proxy", "proxy_username", "proxy_password"):
        if key in options:
            value = options.get(key, "")
            masked[key] = _mask_value(value) if _is_sensitive_key(key) else value
    return masked


def _prompt_proxy_options(
    existing_options: dict[str, str], current_options: dict[str, str]
) -> dict[str, str]:
    proxy_keys = {"proxy", "proxy_username", "proxy_password"}
    existing_proxy = existing_options.get("proxy") or ""
    existing_user = existing_options.get("proxy_username") or ""
    existing_pass = existing_options.get("proxy_password") or ""

    if proxy_keys.intersection(current_options):
        masked = _mask_proxy_options(current_options)
        click.echo(f"检测到已有代理配置: {masked}")
        if not ask_confirm("是否修改代理配置?", default=False):
            return current_options
    else:
        if not ask_confirm("是否配置代理?", default=False):
            return current_options

    proxy = ask_text("proxy", default=existing_proxy)
    if not proxy:
        return current_options
    current_options["proxy"] = proxy

    if ask_confirm("代理是否需要认证?", default=bool(existing_user)):
        proxy_user = ask_text("proxy_username", default=existing_user)
        if proxy_user:
            current_options["proxy_username"] = proxy_user
            current_options["proxy_password"] = _prompt_secret_with_optional_default(
                "proxy_password",
                existing_pass,
            )
    return current_options


def _check_binary(name: str) -> str | None:
    return shutil.which(name)


def _format_check(label: str, ok: bool, detail: str | None = None) -> str:
    status = "OK" if ok else "MISSING"
    base = f"{label}: {status}"
    if detail:
        return f"{base} ({detail})"
    return base


def _is_process_running() -> bool | None:
    if shutil.which("pgrep") is None:
        return None
    result = subprocess.run(
        ["pgrep", "-f", "cc-connect"], capture_output=True, text=True
    )
    return result.returncode == 0


def _stream_process(cmd: Iterable[str], env: dict[str, str]) -> int:
    _ensure_parent(DEFAULT_LOG_FILE)
    with DEFAULT_LOG_FILE.open("a", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            list(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )
        try:
            if process.stdout:
                for line in process.stdout:
                    click.echo(line, nl=False)
                    log_file.write(line)
                    log_file.flush()
            return process.wait()
        except KeyboardInterrupt:
            click.echo("\n已收到中断信号，正在退出...")
            process.terminate()
            return process.wait()


def _notify_start_failure(
    *,
    attempt: int,
    max_failures: int,
    reason: str,
    retry_delay: float,
) -> None:
    click.secho(
        f"cc-connect 启动失败 ({attempt}/{max_failures}): {reason}",
        fg="yellow",
        err=True,
    )
    click.echo(f"日志文件: {DEFAULT_LOG_FILE}", err=True)
    if attempt < max_failures:
        click.echo(f"将在 {retry_delay:g} 秒后重试...", err=True)


def _run_with_retries(
    *,
    cmd: list[str],
    env: dict[str, str],
    max_failures: int,
    retry_delay: float,
) -> None:
    last_reason = ""
    for attempt in range(1, max_failures + 1):
        try:
            exit_code = _stream_process(cmd, env)
        except (OSError, subprocess.SubprocessError) as exc:
            last_reason = str(exc) or exc.__class__.__name__
            _notify_start_failure(
                attempt=attempt,
                max_failures=max_failures,
                reason=last_reason,
                retry_delay=retry_delay,
            )
        else:
            if exit_code == 0:
                click.secho("cc-connect 已正常退出。", fg="green")
                return
            last_reason = f"exit code {exit_code}"
            _notify_start_failure(
                attempt=attempt,
                max_failures=max_failures,
                reason=last_reason,
                retry_delay=retry_delay,
            )

        if attempt < max_failures:
            time.sleep(retry_delay)

    raise click.ClickException(
        f"cc-connect 连续失败 {max_failures} 次，已停止重试。最后错误: {last_reason}"
    )


@cli.command()
@click.option(
    "--interactive/--no-interactive",
    "-i/-I",
    default=None,
    help="Auto prompt on missing args, -i forces interactive, -I disables it.",
)
def setup(interactive: bool | None) -> None:
    """安装/检查 cc-connect 依赖（`chattool setup cc-connect` 的别名）。"""
    from chattool.setup.cc_connect import setup_cc_connect

    setup_cc_connect(interactive=interactive)


@cli.command()
@click.option(
    "--project", default=None, help="Project name (defaults to work dir name)."
)
@click.option(
    "--agent", default=None, type=click.Choice(AGENT_CHOICES), help="Agent type."
)
@click.option(
    "--platform",
    default=None,
    type=click.Choice(PLATFORM_CHOICES),
    help="Platform type.",
)
@click.option(
    "--work-dir",
    default=None,
    type=click.Path(file_okay=False, dir_okay=True),
    help="Agent work dir.",
)
@click.option("--mode", default=None, help="Agent mode (depends on agent type).")
@click.option("--quiet/--no-quiet", default=None, help="Project default quiet mode.")
@click.option(
    "--full-options", is_flag=True, help="Prompt advanced options (e.g. proxy)."
)
@click.option("--config", "-c", default=None, help="Config file path.")
@click.option(
    "--interactive/--no-interactive",
    "-i/-I",
    default=None,
    help="Auto prompt on missing args, -i forces interactive, -I disables it.",
)
def init(
    project: str | None,
    agent: str | None,
    platform: str | None,
    work_dir: str | None,
    mode: str | None,
    quiet: bool | None,
    full_options: bool,
    config: str | None,
    interactive: bool | None,
) -> None:
    """初始化最小可用配置。"""
    from chattool.interaction import (
        abort_if_force_without_tty,
        abort_if_missing_without_tty,
        resolve_interactive_mode,
    )

    config_path = Path(config).expanduser() if config else DEFAULT_CONFIG_FILE
    defaults = _load_existing_defaults(config_path)
    work_dir = work_dir or defaults.get("work_dir") or os.getcwd()
    project = project or defaults.get("project") or Path(work_dir).name or "cc-project"
    default_agent = defaults.get("agent")
    default_platform = defaults.get("platform")
    default_mode = defaults.get("mode")
    default_quiet = defaults.get("quiet")
    if not isinstance(default_quiet, bool):
        default_quiet = None

    effective_agent = agent or default_agent
    effective_platform = platform or default_platform
    platform_from_cli = platform is not None
    agent_from_cli = agent is not None
    missing = []
    if not platform_from_cli:
        missing.append("platform")
    usage = "Usage: chattool cc init [--agent TYPE] [--platform TYPE] [--work-dir PATH] [--project NAME]"
    interactive, can_prompt, force_interactive, _, need_prompt = (
        resolve_interactive_mode(
            interactive=interactive,
            auto_prompt_condition=not (platform_from_cli and agent_from_cli),
        )
    )
    abort_if_force_without_tty(force_interactive, can_prompt, usage)
    abort_if_missing_without_tty(
        missing_required=bool(missing),
        interactive=interactive,
        can_prompt=can_prompt,
        message="Missing required arguments: " + ", ".join(missing),
        usage=usage,
    )

    if config_path.exists():
        if not can_prompt or interactive is False:
            click.echo(f"配置文件已存在: {config_path}", err=True)
            click.echo("请手动删除后重试，或使用交互模式确认覆盖。", err=True)
            raise click.Abort()
        if not ask_confirm(f"配置文件已存在: {config_path}，是否覆盖?", default=False):
            click.echo("已取消")
            return

    if need_prompt:
        if not platform:
            platform = _prompt_choice_text(
                "选择消息平台",
                PLATFORM_CHOICES,
                default=default_platform or "feishu",
            )
        if not agent:
            agent = _prompt_choice_text(
                "选择 Agent 类型",
                AGENT_CHOICES,
                default=default_agent or "claudecode",
            )
        if not mode:
            mode_choices = AGENT_MODE_CHOICES.get(agent or "")
            if mode_choices:
                mode_default = default_mode or AGENT_MODE_DEFAULTS.get(
                    agent or "", "default"
                )
                mode = _prompt_choice_text(
                    "选择权限模式",
                    mode_choices,
                    default=mode_default,
                )
        work_dir = ask_text("Agent 工作目录", default=work_dir)
        project = ask_text("项目名称", default=project)
        if quiet is None:
            quiet = ask_confirm(
                "默认 quiet 模式（隐藏思考和工具进度消息）",
                default=default_quiet if default_quiet is not None else False,
            )
    elif mode:
        mode_choices = AGENT_MODE_CHOICES.get(agent or "")
        if mode_choices and mode not in mode_choices:
            raise click.BadParameter(
                f"mode must be one of {', '.join(mode_choices)} for agent {agent}",
                param_hint="--mode",
            )

    platform_options: dict[str, str] = {}
    should_prompt_credentials = (need_prompt or force_interactive) and can_prompt
    if should_prompt_credentials:
        existing_options = (
            defaults.get("platform_options")
            if isinstance(defaults.get("platform_options"), dict)
            else {}
        )
        if existing_options:
            masked = {
                k: (_mask_value(v) if _is_sensitive_key(k) else v)
                for k, v in existing_options.items()
            }
            click.echo(f"检测到已有平台配置: {masked}")
            platform_options = dict(existing_options)
            if ask_confirm("是否填写平台鉴权信息?", default=True):
                platform_options = _prompt_platform_credentials(
                    platform or "feishu", existing_options
                )
        elif ask_confirm("是否填写平台鉴权信息?", default=True):
            platform_options = _prompt_platform_credentials(
                platform or "feishu", existing_options
            )
        if full_options:
            platform_options = _prompt_proxy_options(existing_options, platform_options)

    _write_config(
        config_path=config_path,
        project_name=project,
        quiet=quiet if quiet is not None else default_quiet,
        agent=agent or default_agent or "claudecode",
        work_dir=work_dir,
        mode=mode
        or default_mode
        or AGENT_MODE_DEFAULTS.get(agent or default_agent or "claudecode", "default"),
        platform=platform or default_platform or "feishu",
        platform_options=platform_options,
    )

    click.secho(f"配置已生成: {config_path}", fg="green")
    if platform_options:
        masked = {
            k: (_mask_value(v) if _is_sensitive_key(k) else v)
            for k, v in platform_options.items()
        }
        click.echo(f"平台配置: {masked}")
    click.echo("下一步: chattool cc start")


@cli.command()
@click.option("--config", "-c", default=None, help="配置文件路径")
@click.option("--debug", is_flag=True, help="开启调试日志")
@click.option(
    "--max-failures",
    default=DEFAULT_MAX_FAILURES,
    show_default=True,
    type=click.IntRange(1, None),
    help="连续失败多少次后停止重试。",
)
@click.option(
    "--retry-delay",
    default=DEFAULT_RETRY_DELAY,
    show_default=True,
    type=click.FloatRange(0.0, None),
    help="失败后的重试间隔秒数。",
)
def start(
    config: str | None,
    debug: bool,
    max_failures: int,
    retry_delay: float,
) -> None:
    """启动 cc-connect（前台输出 + 写入日志）。"""
    config_path = Path(config).expanduser() if config else DEFAULT_CONFIG_FILE

    if not config_path.exists():
        click.secho("配置文件不存在，请先运行 `chattool cc init`", fg="red")
        raise click.Abort()

    if not _check_binary("cc-connect"):
        click.secho("未找到 cc-connect，请先运行 `chattool cc setup`", fg="red")
        raise click.Abort()

    env = os.environ.copy()
    if debug:
        env["CC_LOG_LEVEL"] = "debug"

    cmd = ["cc-connect", "-config", str(config_path)]
    click.secho(f"启动 cc-connect (config={config_path})...", fg="green")
    _run_with_retries(
        cmd=cmd,
        env=env,
        max_failures=max_failures,
        retry_delay=retry_delay,
    )


@cli.command()
def status() -> None:
    """查看基本状态。"""
    checks = []
    node_path = _check_binary("node")
    npm_path = _check_binary("npm")
    cc_path = _check_binary("cc-connect")
    checks.append(_format_check("node", bool(node_path), node_path))
    checks.append(_format_check("npm", bool(npm_path), npm_path))
    checks.append(_format_check("cc-connect", bool(cc_path), cc_path))
    checks.append(
        _format_check("config", DEFAULT_CONFIG_FILE.exists(), str(DEFAULT_CONFIG_FILE))
    )

    running = _is_process_running()
    if running is None:
        checks.append("process: UNKNOWN (pgrep not found)")
    else:
        checks.append(f"process: {'RUNNING' if running else 'NOT RUNNING'}")

    for line in checks:
        click.echo(line)


@cli.command()
@click.option("--follow", "-f", is_flag=True, help="实时查看")
def logs(follow: bool) -> None:
    """查看 cc-connect 日志。"""
    if not DEFAULT_LOG_FILE.exists():
        click.echo(f"未找到日志文件: {DEFAULT_LOG_FILE}")
        click.echo("请先运行 `chattool cc start` 生成日志。")
        return

    if not follow:
        click.echo(DEFAULT_LOG_FILE.read_text(encoding="utf-8"))
        return

    import time

    click.echo(f"实时跟随日志: {DEFAULT_LOG_FILE}")
    with DEFAULT_LOG_FILE.open("r", encoding="utf-8") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if line:
                click.echo(line, nl=False)
            else:
                time.sleep(0.2)


@cli.command()
def doctor() -> None:
    """快速自检。"""
    results = []
    node_path = _check_binary("node")
    npm_path = _check_binary("npm")
    cc_path = _check_binary("cc-connect")
    results.append(_format_check("node", bool(node_path), node_path))
    results.append(_format_check("npm", bool(npm_path), npm_path))
    results.append(_format_check("cc-connect", bool(cc_path), cc_path))
    results.append(
        _format_check("config", DEFAULT_CONFIG_FILE.exists(), str(DEFAULT_CONFIG_FILE))
    )

    config_ok = False
    if DEFAULT_CONFIG_FILE.exists():
        content = DEFAULT_CONFIG_FILE.read_text(encoding="utf-8")
        config_ok = "[[projects]]" in content and "[projects.agent]" in content
    results.append(_format_check("config-format", config_ok))

    for line in results:
        click.echo(line)
