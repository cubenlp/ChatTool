from __future__ import annotations

import hashlib
import os
import shlex
import shutil
import stat
import subprocess
import urllib.request
from pathlib import Path

import click

from chattool.config import BaseEnvConfig, FeishuConfig, OpenAIConfig
from chatenv.source_chain import split_config_sources
from chattool.const import CHATARCH_ENV_DIR
from chattool.interaction import abort_if_force_without_tty, resolve_interactive_mode, resolve_value
from chattool.utils.custom_logger import setup_logger

logger = setup_logger("setup_hermes")

OFFICIAL_INSTALLER_URL = (
    "https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh"
)
DEFAULT_MODEL = "gpt-5.4-mini"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_WEBUI_HOST = "127.0.0.1"
DEFAULT_WEBUI_PORT = 8787


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


def _display_command(command: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in command)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _cache_installer_path() -> Path:
    return Path.home() / ".cache" / "chattool" / "hermes" / "install.sh"


def _packaged_installer_path() -> Path:
    return Path(__file__).resolve().parent / "assets" / "hermes" / "install.sh"


def _download_installer() -> Path:
    target = _cache_installer_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".tmp")
    logger.info("Downloading Hermes installer")
    with urllib.request.urlopen(OFFICIAL_INSTALLER_URL, timeout=60) as response:
        tmp.write_bytes(response.read())
    tmp.chmod(stat.S_IRUSR | stat.S_IWUSR)
    tmp.replace(target)
    return target


def _resolve_installer(installer: str | None, update_installer: bool) -> Path:
    if installer:
        path = Path(installer).expanduser()
        if not path.is_file():
            raise click.ClickException(f"Hermes installer not found: {path}")
        return path

    if update_installer:
        return _download_installer()

    cached = _cache_installer_path()
    if cached.is_file():
        return cached

    packaged = _packaged_installer_path()
    if packaged.is_file():
        return packaged

    raise click.ClickException(
        "Hermes installer is unavailable. Pass --installer PATH or run with --update-installer."
    )


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


def _read_hermes_config(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    section = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not raw_line.startswith((" ", "\t")) and stripped.endswith(":"):
            section = stripped[:-1]
            continue
        if section == "model" and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key == "default":
                values["model"] = value
            elif key == "base_url":
                values["base_url"] = value
    return values


def _openai_values(env_ref: str | None, hermes_home: Path) -> dict[str, str | None]:
    system_values, typed_values = split_config_sources(OpenAIConfig, CHATARCH_ENV_DIR)
    override = _load_env_ref(OpenAIConfig, env_ref)
    existing_env = _read_simple_env(hermes_home / ".env")
    existing_config = _read_hermes_config(hermes_home / "config.yaml")
    return {
        "api_key": resolve_value(
            override.get("OPENAI_API_KEY"),
            existing_env.get("OPENAI_API_KEY"),
            system_values.get("OPENAI_API_KEY"),
            typed_values.get("OPENAI_API_KEY"),
        ),
        "base_url": resolve_value(
            override.get("OPENAI_API_BASE"),
            override.get("OPENAI_BASE_URL"),
            existing_env.get("OPENAI_BASE_URL"),
            existing_env.get("OPENAI_API_BASE"),
            existing_config.get("base_url"),
            system_values.get("OPENAI_API_BASE"),
            system_values.get("OPENAI_BASE_URL"),
            typed_values.get("OPENAI_API_BASE"),
            typed_values.get("OPENAI_BASE_URL"),
            DEFAULT_BASE_URL,
        ),
        "model": resolve_value(
            override.get("OPENAI_API_MODEL"),
            existing_env.get("OPENAI_API_MODEL"),
            existing_config.get("model"),
            system_values.get("OPENAI_API_MODEL"),
            typed_values.get("OPENAI_API_MODEL"),
            DEFAULT_MODEL,
        ),
    }


def _feishu_values(env_ref: str | None) -> dict[str, str | None]:
    if not env_ref:
        return {}
    system_values, typed_values = split_config_sources(FeishuConfig, CHATARCH_ENV_DIR)
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


def _quote_env_value(value: str) -> str:
    if not any(ch.isspace() for ch in value) and not any(ch in value for ch in "'\"#"):
        return value
    return repr(value)


def _upsert_env_values(path: Path, values: dict[str, str]) -> list[str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    remaining = {key: value for key, value in values.items() if value is not None}
    changed: list[str] = []
    output: list[str] = []

    for raw_line in existing_lines:
        stripped = raw_line.strip()
        prefix = ""
        parse_line = stripped
        if stripped.startswith("export "):
            prefix = "export "
            parse_line = stripped[7:].strip()
        if not parse_line or parse_line.startswith("#") or "=" not in parse_line:
            output.append(raw_line)
            continue
        key, old_value = parse_line.split("=", 1)
        key = key.strip()
        if key not in remaining:
            output.append(raw_line)
            continue
        new_value = str(remaining.pop(key))
        normalized_old = old_value.strip().strip('"').strip("'")
        if normalized_old != new_value:
            changed.append(key)
        output.append(f"{prefix}{key}={_quote_env_value(new_value)}")

    for key, value in remaining.items():
        changed.append(key)
        output.append(f"{key}={_quote_env_value(str(value))}")

    path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    return changed


def _yaml_value(value: str | bool | int) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return repr(str(value))


def _upsert_model_config(path: Path, values: dict[str, str]) -> list[str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    output: list[str] = []
    changed: list[str] = []
    in_model = False
    saw_model_section = False
    seen: set[str] = set()

    for raw_line in lines:
        stripped = raw_line.strip()
        is_top_section = bool(stripped) and not raw_line.startswith((" ", "\t")) and stripped.endswith(":")
        if is_top_section:
            if in_model:
                for key, value in values.items():
                    if key not in seen:
                        output.append(f"  {key}: {_yaml_value(value)}")
                        changed.append(f"model.{key}")
            in_model = stripped[:-1] == "model"
            saw_model_section = saw_model_section or in_model
            seen = set() if in_model else seen
            output.append(raw_line)
            continue

        if in_model and ":" in stripped and not stripped.startswith("#"):
            key, old_value = stripped.split(":", 1)
            key = key.strip()
            if key in values:
                seen.add(key)
                new_value = str(values[key])
                normalized_old = old_value.strip().strip('"').strip("'")
                if normalized_old != new_value:
                    changed.append(f"model.{key}")
                indent = raw_line[: len(raw_line) - len(raw_line.lstrip())] or "  "
                output.append(f"{indent}{key}: {_yaml_value(new_value)}")
                continue

        output.append(raw_line)

    if saw_model_section and in_model:
        for key, value in values.items():
            if key not in seen:
                output.append(f"  {key}: {_yaml_value(value)}")
                changed.append(f"model.{key}")

    if not saw_model_section:
        if output and output[-1].strip():
            output.append("")
        output.append("model:")
        for key, value in values.items():
            output.append(f"  {key}: {_yaml_value(value)}")
            changed.append(f"model.{key}")

    path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
    path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    return changed


def _hermes_installed(hermes_home: Path) -> bool:
    return bool(shutil.which("hermes")) or hermes_home.exists()


def _run_installer(installer_path: Path, hermes_home: Path) -> None:
    env = os.environ.copy()
    env["HERMES_HOME"] = str(hermes_home)
    command = ["bash", str(installer_path)]
    click.echo(f"Running Hermes installer: {_display_command(command)}")
    result = subprocess.run(command, env=env, text=True)
    if result.returncode != 0:
        raise click.ClickException(f"Hermes installer failed: {installer_path}")


def _resolve_agent_dir() -> str:
    hermes_bin = shutil.which("hermes")
    if not hermes_bin:
        return ""
    resolved = Path(hermes_bin).resolve()
    if len(resolved.parents) >= 3 and resolved.parent.name == "bin":
        return str(resolved.parents[1])
    return str(resolved.parent)


def _webui_env_values(
    webui_dir: Path | None,
    hermes_home: Path,
    *,
    host: str,
    port: int,
    state_dir: Path | None,
    workspace: Path | None,
    model: str,
    password: str | None,
) -> dict[str, str]:
    values = {
        "HERMES_WEBUI_AGENT_DIR": _resolve_agent_dir(),
        "HERMES_WEBUI_PYTHON": shutil.which("python3") or shutil.which("python") or "",
        "HERMES_WEBUI_HOST": host,
        "HERMES_WEBUI_PORT": str(port),
        "HERMES_WEBUI_STATE_DIR": str(state_dir or hermes_home / "webui-mvp"),
        "HERMES_WEBUI_DEFAULT_WORKSPACE": str(workspace or Path.home() / "workspace"),
        "HERMES_WEBUI_DEFAULT_MODEL": model,
        "HERMES_HOME": str(hermes_home),
        "HERMES_CONFIG_PATH": str(hermes_home / "config.yaml"),
    }
    if webui_dir:
        values["HERMES_WEBUI_DIR"] = str(webui_dir)
    if password:
        values["HERMES_WEBUI_PASSWORD"] = password
    return {key: value for key, value in values.items() if value}


def _write_webui_env(hermes_home: Path, values: dict[str, str]) -> Path:
    env_path = hermes_home / "webui.env"
    changed = _upsert_env_values(env_path, values)
    click.echo(f"WebUI env: {env_path}")
    if changed:
        click.echo("Updated WebUI keys: " + ", ".join(sorted(changed)))
    return env_path


def _start_webui(webui_dir: Path, env_values: dict[str, str]) -> None:
    if not webui_dir.is_dir():
        raise click.ClickException(
            f"Hermes WebUI app files not found: {webui_dir}. Pass --webui-dir with an existing hermes-webui directory."
        )

    env = os.environ.copy()
    env.update(env_values)
    if (webui_dir / "ctl.sh").is_file():
        command = ["./ctl.sh", "start"]
    elif (webui_dir / "start.sh").is_file():
        command = ["./start.sh"]
    elif (webui_dir / "bootstrap.py").is_file():
        command = [env_values.get("HERMES_WEBUI_PYTHON") or "python3", "bootstrap.py"]
    else:
        raise click.ClickException(
            f"No native Hermes WebUI entrypoint found in {webui_dir}."
        )

    click.echo(f"Starting Hermes WebUI: {_display_command(command)}")
    result = subprocess.run(command, cwd=str(webui_dir), env=env, text=True)
    if result.returncode != 0:
        raise click.ClickException("Hermes WebUI start failed.")
    click.echo(f"http://{env_values['HERMES_WEBUI_HOST']}:{env_values['HERMES_WEBUI_PORT']}")


def setup_hermes(
    installer=None,
    update_installer=False,
    hermes_home=None,
    webui_dir=None,
    openai_env=None,
    feishu_env=None,
    api_key=None,
    base_url=None,
    model=None,
    skip_feishu=False,
    with_webui_env=False,
    start_webui=False,
    install_only=False,
    webui_host=DEFAULT_WEBUI_HOST,
    webui_port=DEFAULT_WEBUI_PORT,
    webui_state_dir=None,
    webui_workspace=None,
    webui_model=None,
    webui_password=None,
    interactive=None,
    log_level="INFO",
):
    _configure_logger(log_level)
    usage = "Usage: chattool setup hermes [--installer PATH] [--update-installer] [-e OPENAI_ENV] [-i|-I]"
    interactive, can_prompt, force_interactive, _, _ = resolve_interactive_mode(
        interactive=interactive,
        auto_prompt_condition=False,
    )
    abort_if_force_without_tty(force_interactive, can_prompt, usage)

    hermes_home_path = Path(hermes_home or os.getenv("HERMES_HOME", str(Path.home() / ".hermes"))).expanduser()
    installer_path = _resolve_installer(installer, update_installer)
    click.echo(f"Hermes installer: {installer_path}")
    click.echo(f"Installer sha256: {_sha256(installer_path)}")
    click.echo(f"Hermes home: {hermes_home_path}")

    installed = _hermes_installed(hermes_home_path)
    if installed:
        click.echo("Hermes environment detected; skipping installer and configuring existing environment.")
    else:
        _run_installer(installer_path, hermes_home_path)

    if install_only:
        click.echo("Hermes install-only completed.")
        return

    openai = _openai_values(openai_env, hermes_home_path)
    final_api_key = resolve_value(api_key, openai.get("api_key"))
    final_base_url = resolve_value(base_url, openai.get("base_url"), DEFAULT_BASE_URL)
    final_model = resolve_value(model, openai.get("model"), DEFAULT_MODEL)
    env_values: dict[str, str] = {
        "OPENAI_BASE_URL": final_base_url,
        "OPENAI_API_MODEL": final_model,
    }
    if final_api_key:
        env_values["OPENAI_API_KEY"] = final_api_key

    if feishu_env and not skip_feishu:
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

    changed_env = _upsert_env_values(hermes_home_path / ".env", env_values)
    provider = "custom" if final_base_url and "api.openai.com" not in final_base_url else "openai"
    changed_config = _upsert_model_config(
        hermes_home_path / "config.yaml",
        {"default": final_model, "provider": provider, "base_url": final_base_url},
    )
    click.echo(f"Configured Hermes model: {final_model} ({provider})")
    if changed_env:
        public_keys = [key for key in changed_env if "KEY" not in key and "SECRET" not in key]
        secret_keys = [key for key in changed_env if key not in public_keys]
        if public_keys:
            click.echo("Updated env keys: " + ", ".join(sorted(public_keys)))
        if secret_keys:
            click.echo("Updated secret keys: " + ", ".join(sorted(secret_keys)))
    if changed_config:
        click.echo("Updated config keys: " + ", ".join(sorted(changed_config)))
    if final_api_key:
        click.echo(f"Configured OpenAI key: {_mask_secret(final_api_key)}")

    if webui_host == "0.0.0.0" and not webui_password:
        raise click.ClickException(
            "--webui-host 0.0.0.0 requires --webui-password because it exposes Hermes WebUI beyond localhost."
        )
    if webui_host == "0.0.0.0":
        click.echo("Warning: Hermes WebUI is exposed on 0.0.0.0. Use a strong password and HTTPS/tunnel protection.")

    should_handle_webui = with_webui_env or start_webui
    webui_path = Path(webui_dir).expanduser().resolve() if webui_dir else None
    webui_values = _webui_env_values(
        webui_path,
        hermes_home_path,
        host=webui_host,
        port=webui_port,
        state_dir=Path(webui_state_dir).expanduser() if webui_state_dir else None,
        workspace=Path(webui_workspace).expanduser() if webui_workspace else None,
        model=webui_model or final_model,
        password=webui_password,
    )
    if should_handle_webui:
        _write_webui_env(hermes_home_path, webui_values)
        if webui_path and webui_path.is_dir():
            _upsert_env_values(webui_path / ".env", webui_values)
        elif with_webui_env:
            click.echo("Hermes WebUI app files not found; provide --webui-dir to write app-local .env or start WebUI.")

    if start_webui:
        if not webui_path:
            raise click.ClickException(
                "Missing WebUI app files. Pass --webui-dir with an existing hermes-webui directory."
            )
        _start_webui(webui_path, webui_values)

    click.echo("Hermes setup completed.")
