DEFAULT_BASE_URL = "https://api.anthropic.com/v1"
DEFAULT_SMALL_FAST_MODEL = "claude-3-5-haiku-20241022"


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


def setup_claude(auth_token=None, base_url=None, small_fast_model=None, interactive=None, assume_yes=False):
    import json
    import shutil
    import subprocess
    from pathlib import Path

    import click

    from chattool.utils.tui import BACK_VALUE, ask_confirm, ask_text, is_interactive_available

    click.echo("Starting Claude Code setup...")

    claude_dir = Path.home() / ".claude"
    existing = _load_existing_claude_config(claude_dir)
    existing_auth = existing.get("auth_token")

    ctx = click.get_current_context(silent=True)
    if ctx:
        try:
            if ctx.get_parameter_source("interactive") == click.core.ParameterSource.DEFAULT:
                interactive = None
        except Exception:
            pass

    if isinstance(auth_token, str) and not auth_token.strip():
        auth_token = None
    if isinstance(base_url, str) and not base_url.strip():
        base_url = None
    if isinstance(small_fast_model, str) and not small_fast_model.strip():
        small_fast_model = None

    auth_token = auth_token or existing_auth
    missing_required = not auth_token
    has_existing_config = any(value for value in existing.values())
    can_prompt = is_interactive_available()
    force_interactive = interactive is True
    auto_interactive = interactive is None and can_prompt and (missing_required or has_existing_config)
    need_prompt = force_interactive or auto_interactive

    if force_interactive and not can_prompt:
        click.echo("Interactive mode was requested, but no TTY is available in current terminal.", err=True)
        click.echo(
            "Usage: chattool setup claude [--auth-token <value>] [--base-url <value>] "
            "[--small-fast-model <value>] [-i|-I]",
            err=True,
        )
        raise click.Abort()

    if need_prompt:
        click.echo("Interactive input enabled. Collecting configuration values...")
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
        click.echo("Missing auth token.", err=True)
        raise click.Abort()

    if not shutil.which("npm"):
        click.echo("npm not found. Please run: chattool setup nodejs", err=True)
        raise click.Abort()

    def _npm_bin_has(binary_name):
        try:
            result = subprocess.run(["npm", "bin", "-g"], capture_output=True, text=True)
        except Exception:
            return False
        if result.returncode != 0:
            return False
        bin_dir = result.stdout.strip()
        if not bin_dir:
            return False
        return (Path(bin_dir) / binary_name).exists()

    def _npm_has_package(package_name):
        try:
            result = subprocess.run(
                ["npm", "list", "-g", "--depth=0", package_name],
                capture_output=True,
                text=True,
            )
        except Exception:
            return False
        return result.returncode == 0

    claude_binary = shutil.which("claude") or shutil.which("claude-code")
    npm_bin_has = False
    npm_pkg_has = False
    if not claude_binary:
        npm_bin_has = _npm_bin_has("claude") or _npm_bin_has("claude-code")
        if not npm_bin_has:
            npm_pkg_has = _npm_has_package("@anthropic-ai/claude-code")

    claude_code_installed = bool(claude_binary or npm_bin_has or npm_pkg_has)
    can_prompt_install = can_prompt and interactive is not False
    should_install = True
    if claude_code_installed:
        if claude_binary:
            click.echo(f"Detected claude binary at: {claude_binary}")
        elif npm_bin_has:
            click.echo("Detected claude-code in npm global bin.")
        else:
            click.echo("Detected @anthropic-ai/claude-code in global npm packages.")
        if assume_yes:
            click.echo("claude-code already installed; skipping npm install due to -y/--yes.")
            should_install = False
        elif not can_prompt_install:
            click.echo("claude-code already installed; skipping npm install (non-interactive).")
            should_install = False
        else:
            reinstall = ask_confirm("claude-code already installed. Reinstall via npm?", default=False)
            if not reinstall:
                click.echo("Skipping claude-code installation.")
                should_install = False

    if should_install:
        click.echo("Installing claude-code via npm...")
        install_cmd = ["npm", "install", "-g", "@anthropic-ai/claude-code"]
        result = subprocess.run(install_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            click.echo("Failed to install claude-code.", err=True)
            if result.stderr:
                click.echo(result.stderr.strip(), err=True)
            raise click.Abort()
        click.echo("claude-code installation completed.")

    base_url = base_url or existing.get("base_url") or DEFAULT_BASE_URL
    small_fast_model = small_fast_model or existing.get("small_fast_model") or DEFAULT_SMALL_FAST_MODEL
    primary_api_key = existing.get("primary_api_key") or "1"

    click.echo("Writing Claude Code configuration files...")
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

    config_json = {"primaryApiKey": primary_api_key}
    config_path = claude_dir / "config.json"
    config_path.write_text(json.dumps(config_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    config_path.chmod(0o600)

    click.echo(f"Base URL: {base_url}")
    click.echo(f"Small/Fast Model: {small_fast_model}")
    click.echo("Claude Code setup completed.")
    click.echo(f"Settings: {settings_path}")
    click.echo(f"Config: {config_path}")
