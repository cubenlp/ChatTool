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

DEFAULT_MODEL = "gpt-5.4"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
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
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            values[(section, key)] = value

        existing["preferred_auth_method"] = values.get((None, "preferred_auth_method"))
        existing["model"] = values.get((None, "model"))
        provider_name = values.get((None, "model_provider"))
        if provider_name:
            existing["base_url"] = values.get((f"model_providers.{provider_name}", "base_url"))
        if not existing["base_url"]:
            for (section_name, key), value in values.items():
                if key == "base_url" and section_name and section_name.startswith("model_providers."):
                    existing["base_url"] = value
                    break

    return existing


def setup_codex(preferred_auth_method=None, base_url=None, model=None, interactive=None):
    codex_dir = Path.home() / ".codex"
    existing = _load_existing_codex_config(codex_dir)
    existing_auth = existing.get("openai_api_key") or existing.get("preferred_auth_method")
    logger.info("Start codex setup")

    if isinstance(base_url, str) and not base_url.strip():
        base_url = None
    if isinstance(model, str) and not model.strip():
        model = None

    auth_method = preferred_auth_method or existing_auth
    missing_required = not auth_method
    has_existing_config = any(
        value for key, value in existing.items() if key != "openai_api_key"
    ) or bool(existing.get("openai_api_key"))
    usage = "Usage: chattool setup codex [--preferred-auth-method <value>] [--base-url <value>] [--model <value>] [-i|-I]"
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
            message="Missing required argument --preferred-auth-method and no TTY is available for interactive prompts.",
            usage=usage,
        )
    except click.Abort:
        logger.error("Missing required argument --preferred-auth-method and no TTY available")
        raise

    ensure_nodejs_requirement(interactive=interactive, can_prompt=can_prompt)

    if need_prompt:
        auth_for_prompt = auth_method
        auth_label = "preferred_auth_method / OPENAI_API_KEY"
        if auth_for_prompt:
            auth_label = f"{auth_label} (current: {_mask_secret(auth_for_prompt)}, enter to keep)"
        auth_method = ask_text(auth_label, password=True)
        if auth_method == BACK_VALUE:
            return
        if not auth_method and auth_for_prompt:
            auth_method = auth_for_prompt

        base_url_default = base_url or existing.get("base_url") or DEFAULT_BASE_URL
        base_url = ask_text("base_url (optional)", default=base_url_default)
        if base_url == BACK_VALUE:
            return

        model_default = model or existing.get("model") or DEFAULT_MODEL
        model = ask_text("default model (optional)", default=model_default)
        if model == BACK_VALUE:
            return

    if not auth_method:
        logger.error("Missing auth method")
        click.echo("Missing auth method.", err=True)
        raise click.Abort()

    install_cmd = ["npm", "install", "-g", "@openai/codex@latest"]
    logger.info("Installing codex cli with npm")
    result = subprocess.run(install_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("Failed to install codex cli")
        click.echo("Failed to install codex.", err=True)
        if result.stderr:
            click.echo(result.stderr.strip(), err=True)
        raise click.Abort()

    base_url = base_url or existing.get("base_url") or DEFAULT_BASE_URL
    model = model or existing.get("model") or DEFAULT_MODEL

    codex_dir.mkdir(parents=True, exist_ok=True)

    config_toml = (
        'model_provider = "crs"\n'
        f'model = "{model}"\n'
        'model_reasoning_effort = "high"\n'
        'disable_response_storage = true\n'
        f'preferred_auth_method = "{auth_method}"\n\n'
        '[model_providers.crs]\n'
        'name = "crs"\n'
        f'base_url = "{base_url}"\n'
        'wire_api = "responses"\n'
        'requires_openai_auth = true\n'
    )
    config_path = codex_dir / "config.toml"
    config_path.write_text(config_toml, encoding="utf-8")
    config_path.chmod(0o600)
    logger.info(f"Wrote config file: {config_path}")

    auth_json = {"OPENAI_API_KEY": auth_method}
    auth_path = codex_dir / "auth.json"
    auth_path.write_text(json.dumps(auth_json, ensure_ascii=False, indent=2), encoding="utf-8")
    auth_path.chmod(0o600)
    logger.info(f"Wrote auth file: {auth_path}")

    click.echo("Codex setup completed.")
    click.echo(f"Config: {config_path}")
    click.echo(f"Auth: {auth_path}")
