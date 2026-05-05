"""Rendering helpers for CLI interaction."""

import click


def get_style():
    """Compatibility shim for older questionary-based callers."""
    return None


def _get_console():
    try:
        from rich.console import Console
    except ImportError:  # pragma: no cover - optional dependency fallback
        return None
    return Console(stderr=True)


def _render_heading(title, subtitle=None):
    console = _get_console()
    if not console:
        if subtitle:
            click.echo(f"\n{title}\n{subtitle}", err=True)
        else:
            click.echo(f"\n{title}", err=True)
        return

    try:
        from rich.panel import Panel
    except ImportError:  # pragma: no cover - optional dependency fallback
        if subtitle:
            click.echo(f"\n{title}\n{subtitle}", err=True)
        else:
            click.echo(f"\n{title}", err=True)
        return

    console.print(
        Panel.fit(
            subtitle or "",
            title=f"[bold cyan]{title}[/bold cyan]",
            border_style="cyan",
            padding=(0, 1),
        )
    )


def _render_note(message):
    console = _get_console()
    if not console:
        click.echo(message, err=True)
        return
    console.print(f"[dim]{message}[/dim]")
