from __future__ import annotations

import os
import shlex
import shutil
import stat
import subprocess
from pathlib import Path

import click

from chattool.config import BaseEnvConfig, FeishuConfig, OpenAIConfig
from chatenv.source_chain import split_config_sources
from chattool.const import CHATARCH_ENV_DIR
from chattool.interaction import abort_if_force_without_tty, resolve_interactive_mode, resolve_value
from chattool.utils.custom_logger import setup_logger

logger = setup_logger("setup_hermes")

AGENT_REPO = "https://github.com/NousResearch/hermes-agent.git"
WEBUI_REPO = "https://github.com/nesquena/hermes-webui.git"
DEFAULT_EXTRAS = "messaging,cli,pty,cron,feishu,web,acp,mcp"
DEFAULT_MODEL = "gpt-5.4-mini"
DEFAULT_BASE_URL = "https://api.openai.com/v1"


def _configure_logger(log_level="INFO"):
    global logger
    logger = setup_logger("setup_hermes", log_level=str(log_level).upper())
    return logger


def _mask_secret(value):
    if not value:
        return ""
    text = str(value)
    if len(text) <= 4:
        return "*" * len(text)
    if len(text) <= 8:
        return f"{text[0]}{'*' * (len(text) - 2)}{text[-1]}"
    return f"{text[:3]}{'*' * (len(text) - 7)}{text[-4:]}"


def _run(command: list[str], cwd: Path | None = None, dry_run: bool = False) -> None:
    display = " ".join(shlex.quote(str(part)) for part in command)
    if cwd:
        click.echo(f"Running: (cd {cwd} && {display})")
    else:
        click.echo(f"Running: {display}")
    if dry_run:
        return
    result = subprocess.run(command, cwd=str(cwd) if cwd else None, text=True)
    if result.returncode != 0:
        raise click.ClickException(f"Command failed: {display}")


def _default_agent_dir() -> Path:
    cwd_candidate = Path.cwd() / "hermes"
    if cwd_candidate.exists():
        return cwd_candidate
    return Path.home() / ".hermes" / "hermes-agent"


def _default_webui_dir() -> Path:
    cwd_candidate = Path.cwd() / "hermes-webui"
    if cwd_candidate.exists():
        return cwd_candidate
    return Path.home() / ".hermes" / "hermes-webui"


def _venv_python(agent_dir: Path) -> Path:
    return agent_dir / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _resolve_profile_env_path(config_cls, env_ref: str) -> Path:
    candidate = Path(env_ref).expanduser()
    if candidate.is_file():
        return candidate
    profile_path = config_cls.get_profile_env_file(CHATARCH_ENV_DIR, env_ref)
    if profile_path.exists():
        return profile_path
    raise click.ClickException(
        f"未找到配置: {env_ref}。可传入 .env 文件路径，或对应类型下保存的 profile 名称。"
    )


def _load_env_ref(config_cls, env_ref: str | None) -> dict[str, str]:
    if not env_ref:
        return {}
    return BaseEnvConfig._read_env_values(_resolve_profile_env_path(config_cls, env_ref))


def _openai_values(env_ref: str | None) -> dict[str, str | None]:
    system_values, typed_values = split_config_sources(
        OpenAIConfig, CHATARCH_ENV_DIR
    )
    override = _load_env_ref(OpenAIConfig, env_ref)
    return {
        "api_key": resolve_value(
            override.get("OPENAI_API_KEY"),
            system_values.get("OPENAI_API_KEY"),
            typed_values.get("OPENAI_API_KEY"),
        ),
        "base_url": resolve_value(
            override.get("OPENAI_API_BASE"),
            override.get("OPENAI_BASE_URL"),
            system_values.get("OPENAI_API_BASE"),
            system_values.get("OPENAI_BASE_URL"),
            typed_values.get("OPENAI_API_BASE"),
            typed_values.get("OPENAI_BASE_URL"),
            DEFAULT_BASE_URL,
        ),
        "model": resolve_value(
            override.get("OPENAI_API_MODEL"),
            system_values.get("OPENAI_API_MODEL"),
            typed_values.get("OPENAI_API_MODEL"),
            DEFAULT_MODEL,
        ),
    }


def _feishu_values(env_ref: str | None) -> dict[str, str | None]:
    system_values, typed_values = split_config_sources(
        FeishuConfig, CHATARCH_ENV_DIR
    )
    override = _load_env_ref(FeishuConfig, env_ref)

    def pick(key: str):
        return resolve_value(override.get(key), system_values.get(key), typed_values.get(key))

    return {
        "app_id": pick("FEISHU_APP_ID"),
        "app_secret": pick("FEISHU_APP_SECRET"),
        "api_base": pick("FEISHU_API_BASE"),
        "default_receiver_id": pick("FEISHU_DEFAULT_RECEIVER_ID"),
        "default_chat_id": pick("FEISHU_DEFAULT_CHAT_ID"),
        "encrypt_key": pick("FEISHU_ENCRYPT_KEY"),
        "verify_token": pick("FEISHU_VERIFY_TOKEN"),
    }


def _read_simple_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key[7:].strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def _write_env(path: Path, values: dict[str, str], dry_run: bool = False) -> None:
    if dry_run:
        click.echo(f"Would write Hermes env: {path}")
        return
    existing = _read_simple_env(path)
    existing.update({k: v for k, v in values.items() if v is not None})
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Generated by chattool setup hermes"]
    for key in sorted(existing):
        lines.append(f"{key}={existing[key]}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def _write_config(path: Path, model: str, provider: str, base_url: str, dry_run: bool = False) -> None:
    if dry_run:
        click.echo(f"Would write Hermes config: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    content = f"""model:
  default: {model!r}
  provider: {provider!r}
  base_url: {base_url!r}
terminal:
  backend: local
  cwd: .
  timeout: 180
display:
  streaming: true
"""
    path.write_text(content, encoding="utf-8")
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def _ensure_repos(agent_dir: Path, webui_dir: Path, with_webui: bool, dry_run: bool) -> None:
    if not agent_dir.exists():
        _run(["git", "clone", AGENT_REPO, str(agent_dir)], dry_run=dry_run)
    else:
        click.echo(f"Hermes agent repo exists: {agent_dir}")
    if with_webui:
        if not webui_dir.exists():
            _run(["git", "clone", WEBUI_REPO, str(webui_dir)], dry_run=dry_run)
        else:
            click.echo(f"Hermes WebUI repo exists: {webui_dir}")


def _install_agent(agent_dir: Path, extras: str, dry_run: bool) -> None:
    uv = shutil.which("uv") or str(Path.home() / ".local" / "bin" / "uv")
    if not dry_run and not Path(uv).exists() and shutil.which("uv") is None:
        raise click.ClickException("uv not found. Install uv first: https://docs.astral.sh/uv/")
    python = _venv_python(agent_dir)
    if not python.exists():
        _run([uv, "venv", "venv", "--python", "3.11"], cwd=agent_dir, dry_run=dry_run)
    spec = f".[{extras}]" if extras else "."
    _run([uv, "pip", "install", "--python", str(python), "-e", spec], cwd=agent_dir, dry_run=dry_run)


def _post_install(agent_dir: Path, hermes_home: Path, dry_run: bool) -> None:
    link = Path.home() / ".local" / "bin" / "hermes"
    hermes_bin = agent_dir / "venv" / "bin" / "hermes"
    for rel in ("cron", "sessions", "logs", "pairing", "hooks", "image_cache", "audio_cache", "memories", "skills"):
        target = hermes_home / rel
        if dry_run:
            click.echo(f"Would ensure directory: {target}")
        else:
            target.mkdir(parents=True, exist_ok=True)
    if dry_run:
        click.echo(f"Would symlink {link} -> {hermes_bin}")
    else:
        link.parent.mkdir(parents=True, exist_ok=True)
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(hermes_bin)
        sync_script = agent_dir / "tools" / "skills_sync.py"
        python = _venv_python(agent_dir)
        if sync_script.exists() and python.exists():
            subprocess.run([str(python), str(sync_script)], cwd=str(agent_dir), check=False)


def _write_webui_env(webui_dir: Path, agent_dir: Path, hermes_home: Path, dry_run: bool) -> None:
    env_path = webui_dir / ".env"
    content = f"""HERMES_WEBUI_AGENT_DIR={agent_dir}
HERMES_WEBUI_PYTHON={_venv_python(agent_dir)}
HERMES_WEBUI_HOST=127.0.0.1
HERMES_WEBUI_PORT=8787
HERMES_WEBUI_STATE_DIR={hermes_home / 'webui'}
HERMES_WEBUI_DEFAULT_WORKSPACE={Path.cwd()}
NO_PROXY=127.0.0.1,localhost
no_proxy=127.0.0.1,localhost
"""
    if dry_run:
        click.echo(f"Would write WebUI env: {env_path}")
        return
    env_path.write_text(content, encoding="utf-8")


def _start_webui(webui_dir: Path, agent_dir: Path, hermes_home: Path, dry_run: bool) -> None:
    if dry_run:
        click.echo("Would start Hermes WebUI on http://127.0.0.1:8787")
        return
    log_file = hermes_home / "webui.log"
    pid_file = hermes_home / "webui.pid"
    if pid_file.exists():
        old_pid = pid_file.read_text(encoding="utf-8").strip()
        if old_pid.isdigit():
            try:
                os.kill(int(old_pid), 0)
                click.echo(f"Hermes WebUI already running: PID {old_pid}")
                return
            except OSError:
                pass
    env = os.environ.copy()
    env.update(
        {
            "HERMES_WEBUI_AGENT_DIR": str(agent_dir),
            "HERMES_WEBUI_PYTHON": str(_venv_python(agent_dir)),
            "HERMES_WEBUI_HOST": "127.0.0.1",
            "HERMES_WEBUI_PORT": "8787",
            "HERMES_WEBUI_STATE_DIR": str(hermes_home / "webui"),
            "HERMES_WEBUI_DEFAULT_WORKSPACE": str(Path.cwd()),
            "NO_PROXY": "127.0.0.1,localhost," + env.get("NO_PROXY", ""),
            "no_proxy": "127.0.0.1,localhost," + env.get("no_proxy", ""),
        }
    )
    hermes_home.mkdir(parents=True, exist_ok=True)
    with log_file.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [
                "setsid",
                str(_venv_python(agent_dir)),
                str(webui_dir / "bootstrap.py"),
                "--no-browser",
                "--foreground",
                "--skip-agent-install",
            ],
            cwd=str(webui_dir),
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    pid_file.write_text(f"{process.pid}\n", encoding="utf-8")
    click.echo(f"Hermes WebUI started: PID {process.pid}")
    click.echo("Open: http://127.0.0.1:8787")


def setup_hermes(
    agent_dir=None,
    webui_dir=None,
    openai_env=None,
    feishu_env=None,
    api_key=None,
    base_url=None,
    model=None,
    skip_feishu=False,
    with_webui=True,
    start_webui=False,
    install_only=False,
    extras=DEFAULT_EXTRAS,
    dry_run=False,
    interactive=None,
    log_level="INFO",
):
    _configure_logger(log_level)
    usage = "Usage: chattool setup hermes [--agent-dir PATH] [--webui-dir PATH] [-e OPENAI_ENV] [--feishu-env REF] [-i|-I]"
    interactive, can_prompt, force_interactive, _, _ = resolve_interactive_mode(
        interactive=interactive,
        auto_prompt_condition=False,
    )
    abort_if_force_without_tty(force_interactive, can_prompt, usage)

    agent_path = Path(agent_dir).expanduser().resolve() if agent_dir else _default_agent_dir().resolve()
    webui_path = Path(webui_dir).expanduser().resolve() if webui_dir else _default_webui_dir().resolve()
    hermes_home = Path(os.getenv("HERMES_HOME", str(Path.home() / ".hermes"))).expanduser()

    click.echo(f"Hermes agent dir: {agent_path}")
    click.echo(f"Hermes WebUI dir: {webui_path}")
    click.echo(f"Hermes home: {hermes_home}")

    _ensure_repos(agent_path, webui_path, with_webui=with_webui, dry_run=dry_run)
    _install_agent(agent_path, extras=extras, dry_run=dry_run)
    _post_install(agent_path, hermes_home=hermes_home, dry_run=dry_run)

    if not install_only:
        openai = _openai_values(openai_env)
        final_api_key = resolve_value(api_key, openai.get("api_key"))
        final_base_url = resolve_value(base_url, openai.get("base_url"), DEFAULT_BASE_URL)
        final_model = resolve_value(model, openai.get("model"), DEFAULT_MODEL)
        env_values: dict[str, str] = {
            "OPENAI_BASE_URL": final_base_url,
            "OPENAI_API_MODEL": final_model,
        }
        if final_api_key:
            env_values["OPENAI_API_KEY"] = final_api_key

        if not skip_feishu:
            feishu = _feishu_values(feishu_env)
            if feishu.get("app_id") and feishu.get("app_secret"):
                env_values.update(
                    {
                        "FEISHU_APP_ID": feishu["app_id"],
                        "FEISHU_APP_SECRET": feishu["app_secret"],
                        "FEISHU_DOMAIN": "lark" if "larksuite" in (feishu.get("api_base") or "").lower() else "feishu",
                        "FEISHU_CONNECTION_MODE": "websocket",
                        "FEISHU_ALLOW_ALL_USERS": "false",
                        "FEISHU_GROUP_POLICY": "open",
                    }
                )
                optional_map = {
                    "encrypt_key": "FEISHU_ENCRYPT_KEY",
                    "verify_token": "FEISHU_VERIFICATION_TOKEN",
                    "default_chat_id": "FEISHU_HOME_CHANNEL",
                    "default_receiver_id": "FEISHU_ALLOWED_USERS",
                }
                for source_key, env_key in optional_map.items():
                    value = feishu.get(source_key)
                    if value:
                        env_values[env_key] = value

        _write_env(hermes_home / ".env", env_values, dry_run=dry_run)
        provider = "custom" if final_base_url and "api.openai.com" not in final_base_url else "openai"
        _write_config(hermes_home / "config.yaml", final_model, provider, final_base_url, dry_run=dry_run)
        click.echo(f"Configured Hermes model: {final_model} ({provider})")
        if final_api_key:
            click.echo(f"Configured OpenAI key: {_mask_secret(final_api_key)}")

    if with_webui:
        _write_webui_env(webui_path, agent_path, hermes_home, dry_run=dry_run)
        if start_webui:
            _start_webui(webui_path, agent_path, hermes_home, dry_run=dry_run)

    click.echo("Hermes setup completed.")
