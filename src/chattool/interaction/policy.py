"""Interactive policy helpers shared across CLI commands."""

import click


def is_interactive_available():
    from .prompt import is_interactive_available as _is_interactive_available

    return _is_interactive_available()


def normalize_interactive(interactive):
    ctx = click.get_current_context(silent=True)
    if ctx:
        try:
            if (
                ctx.get_parameter_source("interactive")
                == click.core.ParameterSource.DEFAULT
            ):
                return None
        except Exception:
            pass
    return interactive


def resolve_interactive_mode(interactive, auto_prompt_condition):
    interactive = normalize_interactive(interactive)
    can_prompt = is_interactive_available()
    force_interactive = interactive is True
    auto_interactive = interactive is None and can_prompt and auto_prompt_condition
    need_prompt = force_interactive or auto_interactive
    return interactive, can_prompt, force_interactive, auto_interactive, need_prompt


def abort_if_force_without_tty(force_interactive, can_prompt, usage):
    if force_interactive and not can_prompt:
        click.echo(
            "Interactive mode was requested, but no TTY is available in current terminal.",
            err=True,
        )
        click.echo(usage, err=True)
        raise click.Abort()


def abort_if_missing_without_tty(
    missing_required, interactive, can_prompt, message, usage
):
    if missing_required and interactive is None and not can_prompt:
        click.echo(message, err=True)
        click.echo(usage, err=True)
        raise click.Abort()
