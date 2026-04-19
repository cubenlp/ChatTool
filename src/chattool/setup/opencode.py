from __future__ import annotations

import json
from pathlib import Path
import click

from chattool.config import BaseEnvConfig, OpenAIConfig
from chattool.config.source_chain import split_config_sources
from chattool.const import CHATTOOL_ENV_DIR, CHATTOOL_ENV_FILE
from chattool.interaction import (
    BACK_VALUE,
    ask_checkbox_with_controls,
    abort_if_force_without_tty,
    abort_if_missing_without_tty,
    create_choice,
    prompt_sensitive_value,
    prompt_text_value,
    resolve_interactive_mode,
    resolve_value,
)
from chattool.setup.mode_prompt import resolve_install_only_mode
from chattool.setup.opencode_chatloop import (
    build_legacy_chatloop_plugin_entry,
    install_chatloop_assets,
    resolve_opencode_home,
)
from chattool.setup.nodejs import (
    ensure_nodejs_requirement,
    run_npm_command,
    should_install_global_npm_package,
)
from chattool.utils.custom_logger import setup_logger

DEFAULT_PROVIDER_ID = "opencode"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_PROVIDER_NPM = "@ai-sdk/openai-compatible"
PLUGIN_PRESETS = {"auto-loop": "opencode-auto-loop"}
logger = setup_logger("setup_opencode")


def _configure_logger(log_level="INFO"):
    global logger
    logger = setup_logger("setup_opencode", log_level=str(log_level).upper())
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


def _extract_model_id(model_value, provider_id):
    if not isinstance(model_value, str):
        return None
    if "/" not in model_value:
        return None
    prefix, model_id = model_value.split("/", 1)
    if prefix != provider_id:
        return None
    return model_id or None


def _snapshot_openai_values() -> dict[str, str | None]:
    return {
        "api_key": OpenAIConfig.OPENAI_API_KEY.value,
        "base_url": OpenAIConfig.OPENAI_API_BASE.value,
        "model": OpenAIConfig.OPENAI_API_MODEL.value,
    }


def _load_saved_openai_values() -> dict[str, str | None]:
    current_values = _snapshot_openai_values()
    try:
        BaseEnvConfig.load_all(CHATTOOL_ENV_DIR, legacy_env_file=CHATTOOL_ENV_FILE)
        return _snapshot_openai_values()
    finally:
        _restore_openai_values(current_values)


def _restore_openai_values(values: dict[str, str | None]) -> None:
    OpenAIConfig.OPENAI_API_KEY.value = values.get("api_key")
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


def _load_existing_opencode_config(config_path, provider_id):
    existing: dict[str, str | None] = {
        "base_url": None,
        "api_key": None,
        "model": None,
    }
    config_data = None

    if config_path.exists():
        try:
            config_data = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            config_data = None

    if isinstance(config_data, dict):
        model_value = config_data.get("model")
        existing["model"] = _extract_model_id(model_value, provider_id)

        provider_config = config_data.get("provider")
        if isinstance(provider_config, dict):
            provider_entry = provider_config.get(provider_id)
            if isinstance(provider_entry, dict):
                options = provider_entry.get("options")
                if isinstance(options, dict):
                    existing["base_url"] = options.get("baseURL") or options.get(
                        "baseUrl"
                    )
                    existing["api_key"] = options.get("apiKey")

                if not existing["model"]:
                    models = provider_entry.get("models")
                    if isinstance(models, dict) and models:
                        existing["model"] = next(iter(models.keys()), None)

    return existing, config_data


def _write_opencode_config(config_path: Path, config_payload: dict) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(config_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    config_path.chmod(0o600)
    logger.info(f"Wrote config file: {config_path}")


def _append_plugin(config_payload: dict, plugin_entry: str) -> None:
    existing_plugins = config_payload.get("plugin")
    if not isinstance(existing_plugins, list):
        existing_plugins = []
    if plugin_entry not in existing_plugins:
        existing_plugins.append(plugin_entry)
    config_payload["plugin"] = existing_plugins


def _remove_plugin(config_payload: dict, plugin_entry: str) -> None:
    existing_plugins = config_payload.get("plugin")
    if not isinstance(existing_plugins, list):
        return
    config_payload["plugin"] = [item for item in existing_plugins if item != plugin_entry]


def _apply_plugin_preset(config_payload: dict, plugin: str | None, opencode_home: Path) -> dict | None:
    if not plugin:
        return None

    if plugin == "chatloop":
        installed = install_chatloop_assets(opencode_home)
        _remove_plugin(config_payload, build_legacy_chatloop_plugin_entry(opencode_home))
        _append_plugin(config_payload, str(installed["plugin_entry"]))
        return {
            "name": plugin,
            "plugin_label": str(installed["plugin_entry"]),
            **installed,
        }

    plugin_name = PLUGIN_PRESETS[plugin]
    _append_plugin(config_payload, plugin_name)
    return {"name": plugin, "plugin_label": plugin_name}


def setup_opencode(
    base_url=None,
    api_key=None,
    model=None,
    env_ref=None,
    plugin=None,
    install_only=False,
    interactive=None,
    log_level="INFO",
):
    _configure_logger(log_level)
    config_dir = resolve_opencode_home()
    config_path = config_dir / "opencode.json"
    provider_id = DEFAULT_PROVIDER_ID
    existing, config_data = _load_existing_opencode_config(config_path, provider_id)
    env_values, typed_env_values = split_config_sources(
        OpenAIConfig,
        CHATTOOL_ENV_DIR,
        legacy_env_file=CHATTOOL_ENV_FILE,
    )
    env_config = _load_openai_values_from_env_ref(env_ref) if env_ref else {}
    logger.info("Start opencode setup")

    if isinstance(base_url, str) and not base_url.strip():
        base_url = None
    if isinstance(api_key, str) and not api_key.strip():
        api_key = None
    if isinstance(model, str) and not model.strip():
        model = None

    base_url = resolve_value(
        base_url,
        env_config.get("base_url"),
        existing.get("base_url"),
        env_values.get("OPENAI_API_BASE"),
        typed_env_values.get("OPENAI_API_BASE"),
    )
    api_key = resolve_value(
        api_key,
        env_config.get("api_key"),
        existing.get("api_key"),
        env_values.get("OPENAI_API_KEY"),
        typed_env_values.get("OPENAI_API_KEY"),
    )
    model = resolve_value(
        model,
        env_config.get("model"),
        existing.get("model"),
        env_values.get("OPENAI_API_MODEL"),
        typed_env_values.get("OPENAI_API_MODEL"),
    )

    missing_required = not (base_url and api_key and model)
    has_existing_config = any(value for value in existing.values())
    usage = (
        "Usage: chattool setup opencode [--base-url <value>] [--api-key <value>] "
        "[--model <value>] [-e <openai-env>] [-i|-I]"
    )
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
            message="Missing required arguments and no TTY is available for interactive prompts.",
            usage=usage,
        )
    except click.Abort:
        logger.error("Missing required arguments and no TTY available")
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
            "opencode-ai",
            "OpenCode CLI",
            interactive=interactive,
            can_prompt=can_prompt,
            default_update=True,
        ):
            logger.info("Installing opencode cli with npm")
            result = run_npm_command(["install", "-g", "opencode-ai"])
            if result.returncode != 0:
                logger.error("Failed to install opencode cli")
                click.echo("Failed to install opencode.", err=True)
                if result.stderr:
                    click.echo(result.stderr.strip(), err=True)
                raise click.Abort()
        plugin_result = None
        if plugin:
            config_payload = config_data if isinstance(config_data, dict) else {}
            config_payload["$schema"] = "https://opencode.ai/config.json"
            plugin_result = _apply_plugin_preset(config_payload, plugin, config_dir)
            _write_opencode_config(config_path, config_payload)
        click.echo("OpenCode CLI install completed.")
        if plugin_result:
            click.echo(f"Enabled OpenCode plugin preset: {plugin_result['plugin_label']}")
            if plugin == "chatloop":
                click.echo(f"ChatLoop plugin: {plugin_result['plugin_dir']}")
                click.echo(f"ChatLoop commands: {plugin_result['commands_dir']}")
        return

    if need_prompt:
        base_url = prompt_text_value("base_url", base_url, fallback=DEFAULT_BASE_URL)
        if base_url == BACK_VALUE:
            return

        api_key = prompt_sensitive_value("api_key", api_key, _mask_secret)
        if api_key == BACK_VALUE:
            return

        model = prompt_text_value("model", model)
        if model == BACK_VALUE:
            return

        if plugin is None:
            selected_plugins = ask_checkbox_with_controls(
                "Select plugins",
                choices=[
                    create_choice(
                        "opencode-auto-loop",
                        "auto-loop",
                    ),
                    create_choice(
                        "chatloop (global PRD-driven loop)",
                        "chatloop",
                    )
                ],
                default_values=[],
                instruction="(Use arrow keys to move, <space> to toggle, <a> to toggle all, <enter> to confirm)",
                select_all_label="Select all plugins",
            )
            if selected_plugins == BACK_VALUE:
                return
            if selected_plugins:
                if len(selected_plugins) > 1:
                    click.echo("Select at most one plugin preset.", err=True)
                    raise click.Abort()
                plugin = selected_plugins[0]

    if not (base_url and api_key and model):
        logger.error("Missing base_url, api_key, or model")
        click.echo("Missing base_url, api_key, or model.", err=True)
        raise click.Abort()

    if should_install_global_npm_package(
        "opencode-ai",
        "OpenCode CLI",
        interactive=interactive,
        can_prompt=can_prompt,
    ):
        logger.info("Installing opencode cli with npm")
        result = run_npm_command(["install", "-g", "opencode-ai"])
        if result.returncode != 0:
            logger.error("Failed to install opencode cli")
            click.echo("Failed to install opencode.", err=True)
            if result.stderr:
                click.echo(result.stderr.strip(), err=True)
            raise click.Abort()

    config_payload = config_data if isinstance(config_data, dict) else {}
    config_payload["$schema"] = "https://opencode.ai/config.json"

    providers = config_payload.get("provider")
    if not isinstance(providers, dict):
        providers = {}
        config_payload["provider"] = providers

    providers[provider_id] = {
        "npm": DEFAULT_PROVIDER_NPM,
        "name": "OpenCode Provider",
        "options": {
            "baseURL": base_url,
            "apiKey": api_key,
        },
        "models": {
            model: {"name": model},
        },
    }

    config_payload["model"] = f"{provider_id}/{model}"

    plugin_result = _apply_plugin_preset(config_payload, plugin, config_dir)

    _write_opencode_config(config_path, config_payload)

    click.echo("OpenCode setup completed.")
    click.echo(f"Config: {config_path}")
    if env_ref:
        click.echo(f"Reused ChatTool OpenAI config: {env_ref}")
    if plugin_result:
        click.echo(f"Enabled OpenCode plugin preset: {plugin_result['plugin_label']}")
        if plugin == "chatloop":
            click.echo(f"ChatLoop plugin: {plugin_result['plugin_dir']}")
            click.echo(f"ChatLoop commands: {plugin_result['commands_dir']}")
