import json
import shutil
import subprocess
from pathlib import Path
import click

from chattool.utils.tui import BACK_VALUE, ask_text, is_interactive_available


def setup_codex(preferred_auth_method=None, interactive=None):
    auth_method = preferred_auth_method
    missing_required = not auth_method
    force_interactive = interactive is True
    auto_interactive = interactive is None and missing_required
    need_prompt = force_interactive or auto_interactive

    if need_prompt and not is_interactive_available():
        if force_interactive:
            click.echo("Interactive mode was requested, but no TTY is available in current terminal.", err=True)
        else:
            click.echo("Missing required argument --preferred-auth-method and no TTY is available for interactive prompts.", err=True)
        click.echo("Usage: chattool setup codex [--preferred-auth-method <value>] [-i|-I]", err=True)
        raise click.Abort()

    if need_prompt:
        auth_method = ask_text("preferred_auth_method / OPENAI_API_KEY", password=True)
        if auth_method == BACK_VALUE:
            return

    if not auth_method:
        click.echo("Missing auth method.", err=True)
        raise click.Abort()

    if not shutil.which("npm"):
        click.echo("npm not found. Please run: chattool setup nodejs", err=True)
        raise click.Abort()

    install_cmd = ["npm", "install", "-g", "@openai/codex@latest"]
    result = subprocess.run(install_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        click.echo("Failed to install codex.", err=True)
        if result.stderr:
            click.echo(result.stderr.strip(), err=True)
        raise click.Abort()

    codex_dir = Path.home() / ".codex"
    codex_dir.mkdir(parents=True, exist_ok=True)

    config_toml = (
        'model_provider = "crs"\n'
        'model = "gpt-5.3-codex"\n'
        'model_reasoning_effort = "high"\n'
        'disable_response_storage = true\n'
        f'preferred_auth_method = "{auth_method}"\n\n'
        '[model_providers.crs]\n'
        'name = "crs"\n'
        'base_url = "https://aispeed.ai/openai"\n'
        'wire_api = "responses"\n'
        'requires_openai_auth = true\n'
    )
    config_path = codex_dir / "config.toml"
    config_path.write_text(config_toml, encoding="utf-8")
    config_path.chmod(0o600)

    auth_json = {"OPENAI_API_KEY": auth_method}
    auth_path = codex_dir / "auth.json"
    auth_path.write_text(json.dumps(auth_json, ensure_ascii=False, indent=2), encoding="utf-8")
    auth_path.chmod(0o600)

    click.echo("Codex setup completed.")
    click.echo(f"Config: {config_path}")
    click.echo(f"Auth: {auth_path}")
