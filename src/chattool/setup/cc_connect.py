import click

from chattool.setup.interactive import abort_if_force_without_tty, resolve_interactive_mode
from chattool.setup.nodejs import (
    ensure_nodejs_requirement,
    run_npm_command,
    should_install_global_npm_package,
)
from chattool.utils.custom_logger import setup_logger

logger = setup_logger("setup_cc_connect")


def setup_cc_connect(interactive=None):
    logger.info("Start cc-connect setup")
    usage = "Usage: chattool setup cc-connect [-i|-I]"
    interactive, can_prompt, force_interactive, _, _ = resolve_interactive_mode(
        interactive=interactive,
        auto_prompt_condition=False,
    )
    abort_if_force_without_tty(force_interactive, can_prompt, usage)

    ensure_nodejs_requirement(interactive=interactive, can_prompt=can_prompt)

    logger.info("Checking cc-connect installation")
    if not should_install_global_npm_package(
        "cc-connect",
        "cc-connect",
        interactive=interactive,
        can_prompt=can_prompt,
    ):
        return

    click.echo("未检测到 cc-connect，正在安装 (npm install -g cc-connect)...")
    logger.info("Installing cc-connect cli with npm")
    result = run_npm_command(["install", "-g", "cc-connect"])
    if result.returncode != 0:
        logger.error("Failed to install cc-connect")
        click.echo("cc-connect 安装失败。", err=True)
        if result.stderr:
            click.echo(result.stderr.strip(), err=True)
        raise click.Abort()

    click.echo("cc-connect 安装完成。")
    logger.info("cc-connect setup completed")
