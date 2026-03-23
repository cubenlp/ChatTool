DEFAULT_BASE_URL = "https://api.anthropic.com/v1"
DEFAULT_SMALL_FAST_MODEL = "claude-opus-4-6"


def _mask_secret(value):
    if not value:
        return ""
    value = str(value)
    if len(value) <= 4:
        return "*" * len(value)
    if len(value) <= 8:
        return f"{value[0]}{'*' * (len(value) - 2)}{value[-1]}"
    return f"{value[:3]}{'*' * (len(value) - 7)}{value[-4:]}"


def _load_existing_claude_config(claude_dir):
    import json

    existing = {
        "auth_token": None,
        "base_url": None,
        "small_fast_model": None,
        "primary_api_key": None,
    }

    settings_path = claude_dir / "settings.json"
    if settings_path.exists():
        try:
            settings_data = json.loads(settings_path.read_text(encoding="utf-8"))
            env = settings_data.get("env", {}) if isinstance(settings_data, dict) else {}
            if isinstance(env, dict):
                existing["auth_token"] = env.get("ANTHROPIC_AUTH_TOKEN")
                existing["base_url"] = env.get("ANTHROPIC_BASE_URL")
                existing["small_fast_model"] = env.get("ANTHROPIC_SMALL_FAST_MODEL")
        except Exception:
            pass

    config_path = claude_dir / "config.json"
    if config_path.exists():
        try:
            config_data = json.loads(config_path.read_text(encoding="utf-8"))
            if isinstance(config_data, dict):
                existing["primary_api_key"] = config_data.get("primaryApiKey")
        except Exception:
            pass

    return existing


def setup_claude(auth_token=None, base_url=None, small_fast_model=None, interactive=None):
    import json
    import subprocess
    from pathlib import Path

    import click

    from chattool.setup.interactive import (
        abort_if_force_without_tty,
        resolve_interactive_mode,
    )
    from chattool.setup.nodejs import ensure_nodejs_requirement
    from chattool.utils.custom_logger import setup_logger
    from chattool.utils.tui import BACK_VALUE, ask_text

    logger = setup_logger("setup_claude")
    claude_dir = Path.home() / ".claude"
    existing = _load_existing_claude_config(claude_dir)
    existing_auth = existing.get("auth_token")
    logger.info("Start claude setup")

    if isinstance(auth_token, str) and not auth_token.strip():
        auth_token = None
    if isinstance(base_url, str) and not base_url.strip():
        base_url = None
    if isinstance(small_fast_model, str) and not small_fast_model.strip():
        small_fast_model = None

    auth_token = auth_token or existing_auth
    missing_required = not auth_token
    has_existing_config = any(value for value in existing.values())
    usage = (
        "Usage: chattool setup claude [--auth-token <value>] [--base-url <value>] "
        "[--small-fast-model <value>] [-i|-I]"
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

    ensure_nodejs_requirement(interactive=interactive, can_prompt=can_prompt)

    if need_prompt:
        auth_for_prompt = auth_token
        auth_label = "ANTHROPIC_AUTH_TOKEN"
        if auth_for_prompt:
            auth_label = f"{auth_label} (current: {_mask_secret(auth_for_prompt)}, enter to keep)"
        auth_token = ask_text(auth_label, password=True)
        if auth_token == BACK_VALUE:
            return
        if not auth_token and auth_for_prompt:
            auth_token = auth_for_prompt

        base_url_default = base_url or existing.get("base_url") or DEFAULT_BASE_URL
        base_url = ask_text("ANTHROPIC_BASE_URL (optional)", default=base_url_default)
        if base_url == BACK_VALUE:
            return

        model_default = small_fast_model or existing.get("small_fast_model") or DEFAULT_SMALL_FAST_MODEL
        small_fast_model = ask_text("ANTHROPIC_SMALL_FAST_MODEL (optional)", default=model_default)
        if small_fast_model == BACK_VALUE:
            return

    if not auth_token:
        logger.error("Missing auth token")
        click.echo("Missing auth token.", err=True)
        raise click.Abort()

    install_cmd = ["npm", "install", "-g", "@anthropic-ai/claude-code"]
    logger.info("Installing claude-code cli with npm")
    result = subprocess.run(install_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("Failed to install claude-code cli")
        click.echo("Failed to install claude-code.", err=True)
        if result.stderr:
            click.echo(result.stderr.strip(), err=True)
        raise click.Abort()

    base_url = base_url or existing.get("base_url") or DEFAULT_BASE_URL
    small_fast_model = small_fast_model or existing.get("small_fast_model") or DEFAULT_SMALL_FAST_MODEL
    primary_api_key = existing.get("primary_api_key") or "1"

    claude_dir.mkdir(parents=True, exist_ok=True)

    settings_json = {
        "env": {
            "ANTHROPIC_AUTH_TOKEN": auth_token,
            "ANTHROPIC_BASE_URL": base_url,
            "ANTHROPIC_SMALL_FAST_MODEL": small_fast_model,
        }
    }
    settings_path = claude_dir / "settings.json"
    settings_path.write_text(json.dumps(settings_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    settings_path.chmod(0o600)
    logger.info(f"Wrote settings file: {settings_path}")

    config_json = {"primaryApiKey": primary_api_key}
    config_path = claude_dir / "config.json"
    config_path.write_text(json.dumps(config_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    config_path.chmod(0o600)
    logger.info(f"Wrote config file: {config_path}")

    click.echo("Claude Code setup completed.")
    click.echo(f"Settings: {settings_path}")
    click.echo(f"Config: {config_path}")
