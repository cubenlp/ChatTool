from __future__ import annotations

from pathlib import Path

import click

from chattool.config import HappyConfig
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

logger = setup_logger("setup_happy")


def _write_active_happy_config() -> Path:
    config_path = HappyConfig.get_active_env_file(CHATTOOL_ENV_DIR)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(HappyConfig.render_env_file(), encoding="utf-8")
    return config_path


def _print_happy_summary(
    server_url: str | None, webapp_url: str | None, home_dir: str | None
) -> None:
    click.echo("Happy setup summary:")
    if server_url is not None or webapp_url is not None or home_dir is not None:
        click.echo("- Saved Happy configuration into ChatTool env storage")
        if server_url is not None:
            click.echo(f"- HAPPY_SERVER_URL={server_url}")
        if webapp_url is not None:
            click.echo(f"- HAPPY_WEBAPP_URL={webapp_url}")
        if home_dir is not None:
            click.echo(f"- HAPPY_HOME_DIR={home_dir}")
    else:
        click.echo("- No Happy server/home values were changed")

    click.echo(
        "- Official mode: keep Happy's own hosted defaults and run `happy auth login`"
    )
    click.echo(
        "- Self-hosted mode: set HAPPY_SERVER_URL / HAPPY_WEBAPP_URL to your own Happy deployment, then run `happy auth login`"
    )
    click.echo("- Suggested next step: chatenv cat -t happy")
    click.echo("- Suggested next step: happy auth login")


def setup_happy(server_url=None, webapp_url=None, home_dir=None, interactive=None):
    logger.info("Start happy setup")
    usage = "Usage: chattool setup happy [--server-url URL] [--webapp-url URL] [--home-dir PATH] [-i|-I]"
    interactive, can_prompt, force_interactive, _, _ = resolve_interactive_mode(
        interactive=interactive,
        auto_prompt_condition=bool(
            HappyConfig.HAPPY_SERVER_URL.value
            or HappyConfig.HAPPY_WEBAPP_URL.value
            or HappyConfig.HAPPY_HOME_DIR.value
        ),
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

    if server_url is not None:
        HappyConfig.HAPPY_SERVER_URL.value = server_url
    if webapp_url is not None:
        HappyConfig.HAPPY_WEBAPP_URL.value = webapp_url
    if home_dir is not None:
        HappyConfig.HAPPY_HOME_DIR.value = home_dir

    if any(value is not None for value in (server_url, webapp_url, home_dir)):
        _write_active_happy_config()

    _print_happy_summary(server_url, webapp_url, home_dir)
