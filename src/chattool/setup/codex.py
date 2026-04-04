from __future__ import annotations

import json
from pathlib import Path
import click

from chattool.config import BaseEnvConfig, OpenAIConfig
from chattool.const import CHATTOOL_ENV_DIR, CHATTOOL_ENV_FILE
from chattool.setup.interactive import (
    abort_if_force_without_tty,
    abort_if_missing_without_tty,
    resolve_interactive_mode,
)
from chattool.setup.nodejs import (
    ensure_nodejs_requirement,
    run_npm_command,
    should_install_global_npm_package,
)
from chattool.setup.config_sources import split_config_sources
from chattool.utils.custom_logger import setup_logger
from chattool.utils.tui import BACK_VALUE, ask_text

DEFAULT_MODEL = "gpt-5.4"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_AUTH_METHOD = "apikey"
logger = setup_logger("setup_codex")


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


def _snapshot_openai_values() -> dict[str, str | None]:
    return {
        "openai_api_key": OpenAIConfig.OPENAI_API_KEY.value,
        "base_url": OpenAIConfig.OPENAI_API_BASE.value,
        "model": OpenAIConfig.OPENAI_API_MODEL.value,
    }


def _restore_openai_values(values: dict[str, str | None]) -> None:
    OpenAIConfig.OPENAI_API_KEY.value = values.get("openai_api_key")
    OpenAIConfig.OPENAI_API_BASE.value = values.get("base_url")
    OpenAIConfig.OPENAI_API_MODEL.value = values.get("model")


def _resolve_openai_env_path(env_ref: str) -> Path:
    candidate = Path(env_ref).expanduser()
    if candidate.is_file():
        return candidate

    profile_path = OpenAIConfig.get_profile_env_file(CHATTOOL_ENV_DIR, env_ref)
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
            CHATTOOL_ENV_DIR,
            override_env_file=env_path,
            legacy_env_file=CHATTOOL_ENV_FILE,
        )
        return _snapshot_openai_values()
    finally:
        _restore_openai_values(current_values)


def setup_codex(
    preferred_auth_method=None,
    base_url=None,
    model=None,
    env_ref=None,
    interactive=None,
):
    codex_dir = Path.home() / ".codex"
    existing = _load_existing_codex_config(codex_dir)
    env_values, typed_env_values = split_config_sources(
        OpenAIConfig,
        CHATTOOL_ENV_DIR,
        legacy_env_file=CHATTOOL_ENV_FILE,
    )
    env_config = _load_openai_values_from_env_ref(env_ref) if env_ref else {}
    existing_api_key = existing.get("openai_api_key")
    logger.info("Start codex setup")

    if isinstance(base_url, str) and not base_url.strip():
        base_url = None
    if isinstance(model, str) and not model.strip():
        model = None

    api_key = (
        preferred_auth_method
        or env_config.get("openai_api_key")
        or existing_api_key
        or env_values.get("OPENAI_API_KEY")
        or typed_env_values.get("OPENAI_API_KEY")
    )
    missing_required = not api_key
    has_existing_config = any(
        value for key, value in existing.items() if key != "openai_api_key"
    ) or bool(existing.get("openai_api_key"))
    usage = "Usage: chattool setup codex [--preferred-auth-method <openai-api-key>] [--base-url <value>] [--model <value>] [-e <openai-env>] [-i|-I]"
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

    ensure_nodejs_requirement(interactive=interactive, can_prompt=can_prompt)

    if need_prompt:
        api_key_for_prompt = api_key
        api_key_label = "OPENAI_API_KEY"
        if api_key_for_prompt:
            api_key_label = f"{api_key_label} (current: {_mask_secret(api_key_for_prompt)}, enter to keep)"
        api_key = ask_text(api_key_label, password=True)
        if api_key == BACK_VALUE:
            return
        if not api_key and api_key_for_prompt:
            api_key = api_key_for_prompt

        base_url_default = (
            base_url
            or env_config.get("base_url")
            or existing.get("base_url")
            or env_values.get("OPENAI_API_BASE")
            or typed_env_values.get("OPENAI_API_BASE")
            or DEFAULT_BASE_URL
        )
        base_url = ask_text("base_url (optional)", default=base_url_default)
        if base_url == BACK_VALUE:
            return

        model_default = (
            model
            or env_config.get("model")
            or existing.get("model")
            or env_values.get("OPENAI_API_MODEL")
            or typed_env_values.get("OPENAI_API_MODEL")
            or DEFAULT_MODEL
        )
        model = ask_text("default model (optional)", default=model_default)
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

    base_url = (
        base_url
        or env_config.get("base_url")
        or existing.get("base_url")
        or env_values.get("OPENAI_API_BASE")
        or typed_env_values.get("OPENAI_API_BASE")
        or DEFAULT_BASE_URL
    )
    model = (
        model
        or env_config.get("model")
        or existing.get("model")
        or env_values.get("OPENAI_API_MODEL")
        or typed_env_values.get("OPENAI_API_MODEL")
        or DEFAULT_MODEL
    )

    codex_dir.mkdir(parents=True, exist_ok=True)

    config_toml = (
        'model_provider = "crs"\n'
        f'model = "{model}"\n'
        'model_reasoning_effort = "high"\n'
        "disable_response_storage = true\n"
        f'preferred_auth_method = "{DEFAULT_AUTH_METHOD}"\n\n'
        "[model_providers.crs]\n"
        'name = "crs"\n'
        f'base_url = "{base_url}"\n'
        'wire_api = "responses"\n'
        "requires_openai_auth = true\n"
    )
    config_path = codex_dir / "config.toml"
    config_path.write_text(config_toml, encoding="utf-8")
    config_path.chmod(0o600)
    logger.info(f"Wrote config file: {config_path}")

    auth_json = {"OPENAI_API_KEY": api_key}
    auth_path = codex_dir / "auth.json"
    auth_path.write_text(
        json.dumps(auth_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    auth_path.chmod(0o600)
    logger.info(f"Wrote auth file: {auth_path}")

    click.echo("Codex setup completed.")
    click.echo(f"Config: {config_path}")
    click.echo(f"Auth: {auth_path}")
