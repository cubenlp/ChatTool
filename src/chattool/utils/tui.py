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
    """Ask a selection question using questionary for arrow-key navigation."""
    import questionary

    normalized = [_normalize_choice(choice) for choice in choices]
    questionary_choices = []
    selectable_count = 0
    for choice in normalized:
        if choice["separator"]:
            questionary_choices.append(questionary.Separator())
            continue
        selectable_count += 1
        questionary_choices.append(
            questionary.Choice(
                title=choice["title"],
                value=choice["value"],
            )
        )

    if selectable_count == 0:
        return BACK_VALUE

    select_style = questionary.Style([
        ("qmark", ""),
        ("question", ""),
        ("answer", ""),
        ("pointer", ""),
        ("highlighted", "noreverse"),
        ("selected", "noreverse"),
        ("separator", "dim"),
        ("instruction", "dim"),
        ("text", ""),
        ("disabled", "italic"),
    ])

    selected = questionary.select(
        message,
        choices=questionary_choices,
        qmark="",
        pointer=">",
        style=select_style,
        use_arrow_keys=True,
        use_jk_keys=True,
        instruction="",
    ).ask()
    if selected is None:
        raise click.Abort()
    return selected


def ask_checkbox(message, choices, default_values=None, style=None):
    """Ask a checkbox question using questionary for multi-select."""
    import questionary
    from questionary.prompts import common as questionary_common

    normalized = [_normalize_choice(choice) for choice in choices]
    questionary_choices = []
    default_set = set(default_values or [])
    for choice in normalized:
        if choice["separator"]:
            questionary_choices.append(questionary.Separator())
            continue
        questionary_choices.append(
            questionary.Choice(
                title=choice["title"],
                value=choice["value"],
                checked=choice["value"] in default_set,
            )
        )

    if not questionary_choices:
        return []

    checkbox_style = questionary.Style([
        ("qmark", ""),
        ("question", ""),
        ("answer", ""),
        ("pointer", ""),
        ("highlighted", "noreverse"),
        ("selected", "noreverse"),
        ("separator", "dim"),
        ("instruction", "dim"),
        ("text", ""),
        ("disabled", "italic"),
    ])

    original_selected = questionary_common.INDICATOR_SELECTED
    original_unselected = questionary_common.INDICATOR_UNSELECTED
    questionary_common.INDICATOR_SELECTED = "[x]"
    questionary_common.INDICATOR_UNSELECTED = "[ ]"
    try:
        selected = questionary.checkbox(
            message,
            choices=questionary_choices,
            qmark="",
            pointer=">",
            style=checkbox_style,
            use_arrow_keys=True,
            use_jk_keys=True,
            instruction="",
        ).ask()
    finally:
        questionary_common.INDICATOR_SELECTED = original_selected
        questionary_common.INDICATOR_UNSELECTED = original_unselected

    if selected is None:
        raise click.Abort()
    return selected


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

    return _prompt()


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

    return _prompt()


def ask_confirm(message, default=True, style=None):
    """Ask a confirmation question using Rich rendering and click.confirm."""
    _render_heading("Confirm", message)

    def _prompt():
        return click.confirm("Continue", default=default, prompt_suffix=" ", err=True)

    return _prompt()
