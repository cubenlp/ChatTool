import getpass
import sys

import click

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
except ImportError:  # pragma: no cover - optional dependency fallback
    Console = None
    Panel = None
    Table = None


BACK_VALUE = "__BACK__"


def get_style():
    """Compatibility shim for older questionary-based callers."""
    return None


def _get_console():
    if Console is None:
        return None
    return Console(stderr=True)


def _prompt_or_back(prompt_fn):
    try:
        return prompt_fn()
    except (click.Abort, EOFError, KeyboardInterrupt):
        return BACK_VALUE


def _render_heading(title, subtitle=None):
    console = _get_console()
    if not console:
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


def is_interactive_available():
    """Check if interactive mode is available."""
    import sys

    return bool(sys.stdin.isatty() and sys.stdout.isatty())


def get_separator():
    """Return a logical separator for select prompts."""
    return {"separator": True}


def create_choice(title, value):
    """Return a logical choice object for select prompts."""
    return {"title": title, "value": value}


def _normalize_choice(choice):
    if isinstance(choice, dict):
        if choice.get("separator"):
            return {"separator": True}
        return {
            "title": str(choice.get("title", choice.get("value", ""))),
            "value": choice.get("value"),
            "separator": False,
        }
    return {
        "title": str(choice),
        "value": choice,
        "separator": False,
    }


def ask_select(message, choices, style=None):
    """Ask a selection question using Rich rendering and click input."""
    normalized = [_normalize_choice(choice) for choice in choices]
    selectable = [choice for choice in normalized if not choice["separator"]]

    if not selectable:
        return BACK_VALUE

    _render_heading("Select Option", message)
    console = _get_console()
    if console:
        table = Table(show_header=True, header_style="bold cyan", box=None, pad_edge=False)
        table.add_column("#", style="bold yellow", width=4)
        table.add_column("Choice", style="white")
        index = 1
        for choice in normalized:
            if choice["separator"]:
                table.add_row("", "[dim]----[/dim]")
                continue
            table.add_row(str(index), choice["title"])
            index += 1
        console.print(table)
    else:
        index = 1
        for choice in normalized:
            if choice["separator"]:
                click.echo("  ----", err=True)
                continue
            click.echo(f"  {index}. {choice['title']}", err=True)
            index += 1

    def _prompt():
        selected_index = click.prompt(
            "Enter choice number",
            type=click.IntRange(1, len(selectable)),
            show_choices=False,
            err=True,
        )
        return selectable[selected_index - 1]["value"]

    return _prompt_or_back(_prompt)


def ask_text(message, default="", password=False, style=None):
    """Ask a text question using Rich rendering and click input."""
    _render_heading("Input", message)
    if default and not password:
        _render_note(f"Press Enter to keep default: {default}")
    elif password and default:
        _render_note("Press Enter to keep the current sensitive value.")

    def _prompt():
        if password:
            value = getpass.getpass("Value: ", stream=sys.stderr)
            if value == "" and default:
                return default
            return value
        return click.prompt(
            "Value",
            default=default,
            show_default=bool(default),
            prompt_suffix=": ",
            err=True,
        )

    return _prompt_or_back(_prompt)


def ask_path(message, default="", style=None):
    """Ask a path question using Rich rendering and click input."""
    _render_heading("Path", message)
    if default:
        _render_note(f"Press Enter to keep default path: {default}")

    def _prompt():
        return click.prompt(
            "Path",
            default=default,
            show_default=bool(default),
            prompt_suffix=": ",
            err=True,
        )

    return _prompt_or_back(_prompt)


def ask_confirm(message, default=True, style=None):
    """Ask a confirmation question using Rich rendering and click.confirm."""
    _render_heading("Confirm", message)

    def _prompt():
        return click.confirm("Continue", default=default, prompt_suffix=" ", err=True)

    return _prompt_or_back(_prompt)
