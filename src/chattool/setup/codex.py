from __future__ import annotations

import json
from pathlib import Path
import click

from chattool.config import BaseEnvConfig, OpenAIConfig
from chatenv.source_chain import split_config_sources
from chattool.const import CHATARCH_ENV_DIR, CHATARCH_ENV_FILE
from chattool.interaction import (
    BACK_VALUE,
    abort_if_force_without_tty,
    abort_if_missing_without_tty,
    prompt_sensitive_value,
    prompt_text_value,
    resolve_interactive_mode,
    resolve_value,
)
from chattool.setup.mode_prompt import resolve_install_only_mode
from chattool.setup.nodejs import (
    ensure_nodejs_requirement,
    run_npm_command,
    should_install_global_npm_package,
)
from chattool.utils.custom_logger import setup_logger

DEFAULT_MODEL = "gpt-5.4"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_AUTH_METHOD = "apikey"
logger = setup_logger("setup_codex")


def _configure_logger(log_level="INFO"):
    global logger
    logger = setup_logger("setup_codex", log_level=str(log_level).upper())
    return logger


def _mask_secret(value):
    if not value:
        return ""
    value = str(value)
    if len(value) <= 4:
        return "*" * len(value)
    if len(value) <= 8:
        return f"{value[0]}{'*' * (len(value) - 2)}{value[-1]}"
    return f"{value[:3]}{'*' * (len(value) - 7)}{value[-4:]}"


def _load_existing_codex_config(codex_dir):
    existing = {
        "preferred_auth_method": None,
        "openai_api_key": None,
        "model": None,
        "base_url": None,
    }

    auth_path = codex_dir / "auth.json"
    if auth_path.exists():
        try:
            auth_data = json.loads(auth_path.read_text(encoding="utf-8"))
            existing["openai_api_key"] = auth_data.get("OPENAI_API_KEY")
        except Exception:
            pass

    config_path = codex_dir / "config.toml"
    if config_path.exists():
        try:
            content = config_path.read_text(encoding="utf-8")
        except Exception:
            content = ""
        section = None
        values = {}
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1].strip()
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            values[(section, key)] = value

        existing["preferred_auth_method"] = values.get((None, "preferred_auth_method"))
        existing["model"] = values.get((None, "model"))
        provider_name = values.get((None, "model_provider"))
        if provider_name:
            existing["base_url"] = values.get(
                (f"model_providers.{provider_name}", "base_url")
            )
        if not existing["base_url"]:
            for (section_name, key), value in values.items():
                if (
                    key == "base_url"
                    and section_name
                    and section_name.startswith("model_providers.")
                ):
                    existing["base_url"] = value
                    break

    return existing


def _toml_value(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    return json.dumps(str(value), ensure_ascii=False)


def _upsert_toml_section(content: str, section: str | None, values: dict) -> tuple[str, list[str]]:
    lines = content.splitlines() if content else []
    output: list[str] = []
    changed: list[str] = []
    current_section: str | None = None
    in_target = section is None
    seen: set[str] = set()
    inserted_root = False

    def flush_missing() -> None:
        for key, value in values.items():
            if key not in seen:
                output.append(f"{key} = {_toml_value(value)}")
                changed.append(key if section is None else f"{section}.{key}")
                seen.add(key)

    for raw_line in lines:
        stripped = raw_line.strip()
        is_section = stripped.startswith("[") and stripped.endswith("]")
        if is_section:
            if section is None and not inserted_root:
                flush_missing()
                inserted_root = True
            elif in_target and section is not None:
                flush_missing()
            current_section = stripped[1:-1].strip()
            in_target = current_section == section
            if in_target:
                seen = set()
            output.append(raw_line)
            continue

        if in_target and "=" in stripped and not stripped.startswith("#"):
            key, old_value = stripped.split("=", 1)
            key = key.strip()
            if key in values:
                seen.add(key)
                new_value = values[key]
                normalized_old = old_value.strip().strip('"').strip("'")
                if normalized_old != str(new_value):
                    changed.append(key if section is None else f"{section}.{key}")
                indent = raw_line[: len(raw_line) - len(raw_line.lstrip())]
                output.append(f"{indent}{key} = {_toml_value(new_value)}")
                continue

        output.append(raw_line)

    if section is None:
        if not inserted_root:
            flush_missing()
    elif any(line.strip() == f"[{section}]" for line in output):
        if in_target:
            flush_missing()
    else:
        if output and output[-1].strip():
            output.append("")
        output.append(f"[{section}]")
        seen = set()
        flush_missing()

    return "\n".join(output).rstrip() + "\n", changed


def _write_codex_config(config_path: Path, *, model: str, base_url: str) -> list[str]:
    content = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    content, changed_root = _upsert_toml_section(
        content,
        None,
        {
            "model_provider": "crs",
            "model": model,
            "preferred_auth_method": DEFAULT_AUTH_METHOD,
        },
    )
    content, changed_provider = _upsert_toml_section(
        content,
        "model_providers.crs",
        {
            "name": "crs",
            "base_url": base_url,
            "wire_api": "responses",
            "requires_openai_auth": True,
        },
    )
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(content, encoding="utf-8")
    config_path.chmod(0o600)
    logger.info(f"Patched config file: {config_path}")
    return changed_root + changed_provider


def _write_codex_auth(auth_path: Path, api_key: str) -> list[str]:
    auth_data = {}
    if auth_path.exists():
        try:
            loaded = json.loads(auth_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                auth_data = loaded
        except Exception:
            auth_data = {}
    old_value = auth_data.get("OPENAI_API_KEY")
    auth_data["OPENAI_API_KEY"] = api_key
    auth_path.parent.mkdir(parents=True, exist_ok=True)
    auth_path.write_text(
        json.dumps(auth_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    auth_path.chmod(0o600)
    logger.info(f"Patched auth file: {auth_path}")
    return ["OPENAI_API_KEY"] if old_value != api_key else []


def _snapshot_openai_values() -> dict[str, str | None]:
    return {
        "openai_api_key": OpenAIConfig.OPENAI_API_KEY.value,
        "base_url": OpenAIConfig.OPENAI_API_BASE.value,
        "model": OpenAIConfig.OPENAI_API_MODEL.value,
    }


def _load_saved_openai_values() -> dict[str, str | None]:
    current_values = _snapshot_openai_values()
    try:
        BaseEnvConfig.load_all(CHATARCH_ENV_DIR)
        return _snapshot_openai_values()
    finally:
        _restore_openai_values(current_values)


def _restore_openai_values(values: dict[str, str | None]) -> None:
    OpenAIConfig.OPENAI_API_KEY.value = values.get("openai_api_key")
    OpenAIConfig.OPENAI_API_BASE.value = values.get("base_url")
    OpenAIConfig.OPENAI_API_MODEL.value = values.get("model")


def _resolve_openai_env_path(env_ref: str) -> Path:
    candidate = Path(env_ref).expanduser()
    if candidate.is_file():
        return candidate

    profile_path = OpenAIConfig.get_profile_env_file(CHATARCH_ENV_DIR, env_ref)
    if profile_path.exists():
        return profile_path

    raise click.ClickException(
        f"未找到 OpenAI 配置: {env_ref}。可传入 .env 文件路径，或 OpenAI 类型下保存的 profile 名称。"
    )


def _load_openai_values_from_env_ref(env_ref: str) -> dict[str, str | None]:
    current_values = _snapshot_openai_values()
    try:
        env_path = _resolve_openai_env_path(env_ref)
        BaseEnvConfig.load_all_with_override(
            CHATARCH_ENV_DIR,
            override_env_file=env_path,
        )
        return _snapshot_openai_values()
    finally:
        _restore_openai_values(current_values)


def setup_codex(
    api_key=None,
    base_url=None,
    model=None,
    env_ref=None,
    install_only=False,
    interactive=None,
    log_level="INFO",
):
    _configure_logger(log_level)
    codex_dir = Path.home() / ".codex"
    existing = _load_existing_codex_config(codex_dir)
    env_values, typed_env_values = split_config_sources(
        OpenAIConfig,
        CHATARCH_ENV_DIR,
    )
    env_config = _load_openai_values_from_env_ref(env_ref) if env_ref else {}
    existing_api_key = existing.get("openai_api_key")
    logger.info("Start codex setup")

    if isinstance(base_url, str) and not base_url.strip():
        base_url = None
    if isinstance(model, str) and not model.strip():
        model = None

    api_key = resolve_value(
        api_key,
        env_config.get("openai_api_key"),
        existing_api_key,
        env_values.get("OPENAI_API_KEY"),
        typed_env_values.get("OPENAI_API_KEY"),
    )
    missing_required = not api_key
    has_existing_config = any(
        value for key, value in existing.items() if key != "openai_api_key"
    ) or bool(existing.get("openai_api_key"))
    usage = "Usage: chattool setup codex [--api-key <openai-api-key>] [--base-url <value>] [--model <value>] [-e <openai-env>] [-i|-I]"
    interactive, can_prompt, force_interactive, auto_interactive, need_prompt = (
        resolve_interactive_mode(
            interactive=interactive,
            auto_prompt_condition=(missing_required or has_existing_config),
        )
    )

    try:
        abort_if_force_without_tty(force_interactive, can_prompt, usage)
    except click.Abort:
        logger.error("Interactive mode requested but no TTY is available")
        raise

    try:
        abort_if_missing_without_tty(
            missing_required=missing_required,
            interactive=interactive,
            can_prompt=can_prompt,
            message="Missing required OpenAI API key and no TTY is available for interactive prompts.",
            usage=usage,
        )
    except click.Abort:
        logger.error("Missing required OpenAI API key and no TTY available")
        raise

    ensure_nodejs_requirement(
        interactive=interactive,
        can_prompt=can_prompt,
        log_level=log_level,
    )

    install_only, aborted = resolve_install_only_mode(
        need_prompt=need_prompt,
        install_only=install_only,
        can_prompt=can_prompt,
    )
    if aborted:
        return

    if install_only:
        if should_install_global_npm_package(
            "@openai/codex",
            "Codex CLI",
            interactive=interactive,
            can_prompt=can_prompt,
            default_update=True,
        ):
            logger.info("Installing codex cli with npm")
            result = run_npm_command(["install", "-g", "@openai/codex@latest"])
            if result.returncode != 0:
                logger.error("Failed to install codex cli")
                click.echo("Failed to install codex.", err=True)
                if result.stderr:
                    click.echo(result.stderr.strip(), err=True)
                raise click.Abort()
        click.echo("Codex CLI install completed.")
        return

    if need_prompt:
        api_key = prompt_sensitive_value("OPENAI_API_KEY", api_key, _mask_secret)
        if api_key == BACK_VALUE:
            return

        base_url = prompt_text_value(
            "base_url (optional)",
            base_url,
            env_config.get("base_url"),
            existing.get("base_url"),
            env_values.get("OPENAI_API_BASE"),
            typed_env_values.get("OPENAI_API_BASE"),
            fallback=DEFAULT_BASE_URL,
        )
        if base_url == BACK_VALUE:
            return

        model = prompt_text_value(
            "default model (optional)",
            model,
            env_config.get("model"),
            existing.get("model"),
            env_values.get("OPENAI_API_MODEL"),
            typed_env_values.get("OPENAI_API_MODEL"),
            fallback=DEFAULT_MODEL,
        )
        if model == BACK_VALUE:
            return

    if not api_key:
        logger.error("Missing OpenAI API key")
        click.echo("Missing OpenAI API key.", err=True)
        raise click.Abort()

    if should_install_global_npm_package(
        "@openai/codex",
        "Codex CLI",
        interactive=interactive,
        can_prompt=can_prompt,
    ):
        logger.info("Installing codex cli with npm")
        result = run_npm_command(["install", "-g", "@openai/codex@latest"])
        if result.returncode != 0:
            logger.error("Failed to install codex cli")
            click.echo("Failed to install codex.", err=True)
            if result.stderr:
                click.echo(result.stderr.strip(), err=True)
            raise click.Abort()

    base_url = resolve_value(
        base_url,
        env_config.get("base_url"),
        existing.get("base_url"),
        env_values.get("OPENAI_API_BASE"),
        typed_env_values.get("OPENAI_API_BASE"),
        DEFAULT_BASE_URL,
    )
    model = resolve_value(
        model,
        env_config.get("model"),
        existing.get("model"),
        env_values.get("OPENAI_API_MODEL"),
        typed_env_values.get("OPENAI_API_MODEL"),
        DEFAULT_MODEL,
    )

    codex_dir.mkdir(parents=True, exist_ok=True)

    config_path = codex_dir / "config.toml"
    changed_config = _write_codex_config(config_path, model=model, base_url=base_url)
    auth_path = codex_dir / "auth.json"
    changed_auth = _write_codex_auth(auth_path, api_key)

    click.echo("Codex setup completed.")
    click.echo(f"Config: {config_path}")
    click.echo(f"Auth: {auth_path}")
    if changed_config:
        click.echo("Updated Codex config keys: " + ", ".join(sorted(changed_config)))
    if changed_auth:
        click.echo("Updated Codex secret keys: " + ", ".join(sorted(changed_auth)))
