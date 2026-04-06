from __future__ import annotations

from pathlib import Path

import click

from chattool.interaction import (
    BACK_VALUE,
    ask_confirm,
    ask_path,
    ask_select,
    ask_text,
    create_choice,
    get_separator,
    is_interactive_available,
)
from chattool.tools.nginx.templates import (
    CATEGORY_LABELS,
    TEMPLATE_SPECS,
    USAGE,
    build_template_values,
    list_templates_by_category,
    parse_set_values,
    render_template,
    resolve_template,
)


def _select_template_interactively() -> str:
    category_choices = [
        create_choice(CATEGORY_LABELS[category], category)
        for category, _ in list_templates_by_category()
    ]
    selected_category = ask_select("选择 Nginx 配置大类", choices=category_choices)
    if selected_category == BACK_VALUE:
        raise click.Abort()

    template_choices = []
    for category, specs in list_templates_by_category():
        if category != selected_category:
            continue
        template_choices.append(get_separator())
        for spec in specs:
            template_choices.append(
                create_choice(f"{spec.name} - {spec.description}", spec.name)
            )

    selected = ask_select("选择具体模板", choices=template_choices)
    if selected == BACK_VALUE:
        raise click.Abort()
    return selected


def _prompt_template_values(
    template_name: str, current_values: dict[str, str]
) -> dict[str, str]:
    spec = TEMPLATE_SPECS[template_name]
    values = dict(current_values)
    fields_by_key = {field.key: field for field in spec.fields}
    click.echo(f"Template: {spec.name} - {spec.title}")
    for key in spec.prompt_fields:
        field = fields_by_key[key]
        values[field.key] = ask_text(
            field.label, default=values.get(field.key, field.default)
        )
    return values


def _write_output(content: str, output_file: str | None, force: bool) -> None:
    if not output_file:
        click.echo(content, nl=False)
        return

    target = Path(output_file).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not force:
        if not is_interactive_available():
            raise click.ClickException(f"Output file already exists: {target}")
        if not ask_confirm(f"{target} exists, overwrite?", default=False):
            click.echo("Cancelled.")
            return
    target.write_text(content, encoding="utf-8")
    click.echo(f"Generated nginx config: {target}")


@click.command(name="nginx")
@click.argument("template", required=False)
@click.argument("output_file", required=False)
@click.option(
    "--interactive/--no-interactive",
    "interactive",
    "-i/-I",
    default=None,
    help="Auto prompt when template is missing, -i forces interactive, -I disables it.",
)
@click.option(
    "--set",
    "set_values",
    multiple=True,
    help="Override template variable, e.g. --set SERVER_NAME=app.example.com",
)
@click.option(
    "--force", is_flag=True, help="Overwrite existing output file without confirm."
)
@click.option(
    "--list", "list_templates", is_flag=True, help="List available nginx templates."
)
def cli(
    template: str | None,
    output_file: str | None,
    interactive: bool | None,
    set_values: tuple[str, ...],
    force: bool,
    list_templates: bool,
) -> None:
    """Generate nginx config templates for common deployment scenarios."""

    if list_templates:
        for category, specs in list_templates_by_category():
            click.echo(f"[{CATEGORY_LABELS[category]}]")
            for spec in specs:
                click.echo(f"- {spec.name}: {spec.description}")
        return

    prompted_template = False
    selected_template = resolve_template(template)
    missing_required = not selected_template
    force_interactive = interactive is True
    auto_interactive = (
        interactive is None and missing_required and is_interactive_available()
    )
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

    if not selected_template and interactive is False:
        click.echo("Missing required argument: template", err=True)
        click.echo(f"Usage: {USAGE}", err=True)
        raise click.Abort()

    if need_prompt and not selected_template:
        selected_template = _select_template_interactively()
        prompted_template = True

    if not selected_template:
        click.echo(f"Usage: {USAGE}", err=True)
        raise click.Abort()

    values = build_template_values(selected_template, parse_set_values(set_values))
    if need_prompt or prompted_template:
        values = _prompt_template_values(selected_template, values)
        if not output_file and ask_confirm(
            "Write generated config to file?", default=False
        ):
            output_file = ask_path(
                "Output file path",
                default=str(Path.cwd() / f"{selected_template}.conf"),
            )

    rendered = render_template(selected_template, values)
    _write_output(rendered, output_file, force=force)


if __name__ == "__main__":
    cli()
