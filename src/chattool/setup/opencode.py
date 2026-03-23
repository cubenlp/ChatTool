import json
import subprocess
from pathlib import Path
import click

from chattool.setup.interactive import (
    abort_if_force_without_tty,
    abort_if_missing_without_tty,
    resolve_interactive_mode,
)
from chattool.setup.nodejs import ensure_nodejs_requirement
from chattool.utils.custom_logger import setup_logger
from chattool.utils.tui import BACK_VALUE, ask_text

DEFAULT_PROVIDER_ID = "opencode"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_PROVIDER_NPM = "@ai-sdk/openai-compatible"
logger = setup_logger("setup_opencode")


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


def _load_existing_opencode_config(config_path, provider_id):
    existing = {
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
                    existing["base_url"] = options.get("baseURL") or options.get("baseUrl")
                    existing["api_key"] = options.get("apiKey")

                if not existing["model"]:
                    models = provider_entry.get("models")
                    if isinstance(models, dict) and models:
                        existing["model"] = next(iter(models.keys()), None)

    return existing, config_data


def setup_opencode(base_url=None, api_key=None, model=None, interactive=None):
    config_dir = Path.home() / ".config" / "opencode"
    config_path = config_dir / "opencode.json"
    provider_id = DEFAULT_PROVIDER_ID
    existing, config_data = _load_existing_opencode_config(config_path, provider_id)
    logger.info("Start opencode setup")

    if isinstance(base_url, str) and not base_url.strip():
        base_url = None
    if isinstance(api_key, str) and not api_key.strip():
        api_key = None
    if isinstance(model, str) and not model.strip():
        model = None

    base_url = base_url or existing.get("base_url")
    api_key = api_key or existing.get("api_key")
    model = model or existing.get("model")

    missing_required = not (base_url and api_key and model)
    has_existing_config = any(value for value in existing.values())
    usage = (
        "Usage: chattool setup opencode [--base-url <value>] [--api-key <value>] "
        "[--model <value>] [-i|-I]"
    )
    interactive, can_prompt, force_interactive, auto_interactive, need_prompt = resolve_interactive_mode(
        interactive=interactive,
        auto_prompt_condition=(missing_required or has_existing_config),
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

    ensure_nodejs_requirement(interactive=interactive, can_prompt=can_prompt)

    if need_prompt:
        base_url_default = base_url or DEFAULT_BASE_URL
        base_url = ask_text("base_url", default=base_url_default)
        if base_url == BACK_VALUE:
            return

        api_key_label = "api_key"
        if api_key:
            api_key_label = f"{api_key_label} (current: {_mask_secret(api_key)}, enter to keep)"
        api_key_input = ask_text(api_key_label, password=True)
        if api_key_input == BACK_VALUE:
            return
        if api_key_input:
            api_key = api_key_input

        model_default = model or ""
        model = ask_text("model", default=model_default)
        if model == BACK_VALUE:
            return

    if not (base_url and api_key and model):
        logger.error("Missing base_url, api_key, or model")
        click.echo("Missing base_url, api_key, or model.", err=True)
        raise click.Abort()

    install_cmd = ["npm", "install", "-g", "opencode-ai"]
    logger.info("Installing opencode cli with npm")
    result = subprocess.run(install_cmd, capture_output=True, text=True)
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

    config_dir.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(config_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    config_path.chmod(0o600)
    logger.info(f"Wrote config file: {config_path}")

    click.echo("OpenCode setup completed.")
    click.echo(f"Config: {config_path}")
