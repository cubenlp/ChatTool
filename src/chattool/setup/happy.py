from __future__ import annotations

from pathlib import Path

import click

from chattool.config import HappyConfig, OpenAIConfig
from chattool.const import CHATTOOL_ENV_DIR
from chattool.setup.interactive import (
    abort_if_force_without_tty,
    resolve_interactive_mode,
)
from chattool.setup.nodejs import (
    ensure_nodejs_requirement,
    run_npm_command,
    should_install_global_npm_package,
)
from chattool.utils.custom_logger import setup_logger
from chattool.utils.tui import BACK_VALUE, ask_text

logger = setup_logger("setup_happy")
HAPPY_PROFILE = "happy"
DEFAULT_HAPPY_MODEL = "gpt-5.4"


def _write_profile(config_cls, profile_name: str) -> Path:
    profile_path = config_cls.get_profile_env_file(CHATTOOL_ENV_DIR, profile_name)
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(config_cls.render_env_file(), encoding="utf-8")
    return profile_path


def _print_happy_summary(write_env: bool) -> None:
    click.echo("Happy coder bootstrap summary:")
    click.echo(
        "- Official hosted mode: keep HAPPY_SERVER_URL / HAPPY_WEBAPP_URL defaults and run `happy auth login`"
    )
    click.echo(
        "- Self-hosted mode: point HAPPY_SERVER_URL / HAPPY_WEBAPP_URL to your own deployment and reuse the same CLI"
    )
    click.echo("- Suggested next step: chatenv use happy -t openai")
    click.echo("- Suggested next step: chattool setup codex -e happy")
    click.echo("- Suggested next step: chattool setup opencode -e happy")
    click.echo("- Suggested next step: chattool setup workspace ~/workspace/happy")
    click.echo("- Suggested next step: happy auth login")
    if write_env:
        click.echo(
            f"- Saved Happy profile: {HappyConfig.get_profile_env_file(CHATTOOL_ENV_DIR, HAPPY_PROFILE)}"
        )
        click.echo(
            f"- Saved OpenAI profile: {OpenAIConfig.get_profile_env_file(CHATTOOL_ENV_DIR, HAPPY_PROFILE)}"
        )
    else:
        click.echo(
            "- Dry guidance only: rerun with --write-env to save dedicated happy profiles."
        )


def setup_happy(
    server_url=None,
    webapp_url=None,
    home_dir=None,
    base_url=None,
    api_key=None,
    model=None,
    write_env=False,
    interactive=None,
):
    logger.info("Start happy setup")
    usage = "Usage: chattool setup happy [--server-url URL] [--webapp-url URL] [--home-dir PATH] [--base-url URL] [--api-key KEY] [--model NAME] [--write-env] [-i|-I]"
    interactive, can_prompt, force_interactive, _, _ = resolve_interactive_mode(
        interactive=interactive,
        auto_prompt_condition=not all([base_url, api_key]),
    )
    abort_if_force_without_tty(force_interactive, can_prompt, usage)

    ensure_nodejs_requirement(interactive=interactive, can_prompt=can_prompt)
    if should_install_global_npm_package(
        "happy", "happy", interactive=interactive, can_prompt=can_prompt
    ):
        click.echo("未检测到 happy，正在安装 (npm install -g happy)...")
        result = run_npm_command(["install", "-g", "happy"])
        if result.returncode != 0:
            click.echo("happy 安装失败。", err=True)
            if result.stderr:
                click.echo(result.stderr.strip(), err=True)
            raise click.Abort()
        click.echo("happy 安装完成。")

    server_url = (
        server_url
        or HappyConfig.HAPPY_SERVER_URL.value
        or "https://api.cluster-fluster.com"
    )
    webapp_url = (
        webapp_url
        or HappyConfig.HAPPY_WEBAPP_URL.value
        or "https://app.happy.engineering"
    )
    home_dir = home_dir or HappyConfig.HAPPY_HOME_DIR.value or ""
    base_url = base_url or OpenAIConfig.OPENAI_API_BASE.value or ""
    api_key = api_key or OpenAIConfig.OPENAI_API_KEY.value or ""
    model = model or OpenAIConfig.OPENAI_API_MODEL.value or DEFAULT_HAPPY_MODEL

    if interactive is not False and can_prompt:
        if not base_url:
            value = ask_text("happy_openai_base_url")
            if value == BACK_VALUE:
                raise click.Abort()
            base_url = str(value).strip()
        if not api_key:
            value = ask_text("happy_openai_api_key", password=True)
            if value == BACK_VALUE:
                raise click.Abort()
            api_key = str(value).strip()

    if not (base_url and api_key):
        click.echo("Missing happy base_url or api_key.", err=True)
        raise click.Abort()

    if write_env:
        HappyConfig.HAPPY_SERVER_URL.value = server_url
        HappyConfig.HAPPY_WEBAPP_URL.value = webapp_url
        HappyConfig.HAPPY_HOME_DIR.value = home_dir
        OpenAIConfig.OPENAI_API_BASE.value = base_url
        OpenAIConfig.OPENAI_API_KEY.value = api_key
        OpenAIConfig.OPENAI_API_MODEL.value = model
        _write_profile(HappyConfig, HAPPY_PROFILE)
        _write_profile(OpenAIConfig, HAPPY_PROFILE)

    _print_happy_summary(write_env)
