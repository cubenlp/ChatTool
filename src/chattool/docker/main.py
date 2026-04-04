from pathlib import Path

import click

from chattool.docker.elements import (
    TEMPLATES,
    USAGE,
    parse_set_values,
    render_env_example,
    resolve_template,
)
from chattool.utils.tui import (
    BACK_VALUE,
    ask_path,
    ask_select,
    is_interactive_available,
)


def docker_main(
    template, output_dir, interactive, set_values, compose_name, env_name, force
):
    selected_template = resolve_template(template)
    selected_output_dir = output_dir

    missing_required = not selected_template or not selected_output_dir
    force_interactive = interactive is True
    auto_interactive = interactive is None and missing_required
    need_prompt = force_interactive or auto_interactive

    if need_prompt and not is_interactive_available():
        if force_interactive:
            click.echo(
                "Interactive mode was requested, but no TTY is available in current terminal.",
                err=True,
            )
        else:
            click.echo(
                "Missing required arguments and no TTY is available for interactive prompts.",
                err=True,
            )
        click.echo(f"Usage: {USAGE}", err=True)
        raise click.Abort()

    if need_prompt:
        if force_interactive or not selected_template:
            selected_template = ask_select(
                "Select docker template:",
                choices=["chromium", "playwright", "headless-chromedriver", "nas"],
            )
            if selected_template == BACK_VALUE:
                return
        if force_interactive or not selected_output_dir:
            selected_output_dir = ask_path(
                "Output directory:",
                default=str(Path(selected_output_dir or Path.cwd())),
            )
            if selected_output_dir == BACK_VALUE:
                return

    if not selected_template or not selected_output_dir:
        click.echo(f"Usage: {USAGE}", err=True)
        raise click.Abort()

    overrides = parse_set_values(set_values)
    target_dir = Path(selected_output_dir).expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    compose_file = target_dir / compose_name
    env_file = target_dir / (env_name or f"{selected_template}.env.example")

    if not force:
        if compose_file.exists() and not click.confirm(
            f"{compose_file} exists, overwrite?", default=False
        ):
            click.echo("Cancelled.")
            return
        if env_file.exists() and not click.confirm(
            f"{env_file} exists, overwrite?", default=False
        ):
            click.echo("Cancelled.")
            return

    compose_file.write_text(TEMPLATES[selected_template], encoding="utf-8")
    env_file.write_text(
        render_env_example(selected_template, overrides), encoding="utf-8"
    )
    click.echo(f"Generated compose: {compose_file}")
    click.echo(f"Generated env example: {env_file}")
    click.echo(f"Template: {selected_template}")
