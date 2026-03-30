import getpass
import sys
from contextlib import contextmanager

import click


BACK_VALUE = "__BACK__"
CHECKBOX_SELECTED_INDICATOR = "[x]"
CHECKBOX_UNSELECTED_INDICATOR = "[ ]"


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


def is_interactive_available():
    """Check if interactive mode is available."""
    return bool(sys.stdin.isatty() and sys.stdout.isatty())


def get_separator():
    """Return a logical separator for select prompts."""
    return {"separator": True}


def create_choice(title, value, checked=False):
    """Return a choice object for select/checkbox prompts."""
    try:
        import questionary
    except ImportError:
        return {"title": title, "value": value, "checked": checked}

    return questionary.Choice(title=title, value=value, checked=checked)


def _normalize_choice(choice):
    if isinstance(choice, dict):
        if choice.get("separator"):
            return {"separator": True}
        return {
            "title": str(choice.get("title", choice.get("value", ""))),
            "value": choice.get("value"),
            "checked": bool(choice.get("checked", False)),
            "separator": False,
        }

    if isinstance(choice, str):
        return {
            "title": choice,
            "value": choice,
            "checked": False,
            "separator": False,
        }

    title = getattr(choice, "title", choice)
    value = getattr(choice, "value", choice)
    checked = bool(getattr(choice, "checked", False))
    return {
        "title": str(title),
        "value": value,
        "checked": checked,
        "separator": False,
    }


def _questionary_select_style(questionary):
    return questionary.Style([
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


def _render_numbered_choices(message, normalized):
    _render_heading("Select Option", message)
    index = 1
    for choice in normalized:
        if choice["separator"]:
            click.echo("  ----", err=True)
            continue
        click.echo(f"  {index}. {choice['title']}", err=True)
        index += 1


def ask_select(message, choices, style=None):
    """Ask a selection question using questionary for arrow-key navigation."""
    normalized = [_normalize_choice(choice) for choice in choices]
    selectable = [choice for choice in normalized if not choice["separator"]]

    if not selectable:
        return BACK_VALUE

    try:
        import questionary
    except ImportError:
        _render_numbered_choices(message, normalized)
        selected_index = click.prompt(
            "Enter choice number",
            type=click.IntRange(1, len(selectable)),
            show_choices=False,
            err=True,
        )
        return selectable[selected_index - 1]["value"]

    questionary_choices = []
    for choice in normalized:
        if choice["separator"]:
            questionary_choices.append(questionary.Separator())
            continue
        questionary_choices.append(
            questionary.Choice(title=choice["title"], value=choice["value"])
        )

    selected = questionary.select(
        message,
        choices=questionary_choices,
        qmark="",
        pointer=">",
        style=style or _questionary_select_style(questionary),
        use_arrow_keys=True,
        use_jk_keys=True,
        instruction="",
    ).ask()
    if selected is None:
        raise click.Abort()
    return selected


@contextmanager
def checkbox_indicator_style():
    """Temporarily render questionary checkboxes with ASCII indicators."""
    import questionary.constants as constants
    import questionary.prompts.common as common

    old_selected = constants.INDICATOR_SELECTED
    old_unselected = constants.INDICATOR_UNSELECTED
    old_common_selected = common.INDICATOR_SELECTED
    old_common_unselected = common.INDICATOR_UNSELECTED

    constants.INDICATOR_SELECTED = CHECKBOX_SELECTED_INDICATOR
    constants.INDICATOR_UNSELECTED = CHECKBOX_UNSELECTED_INDICATOR
    common.INDICATOR_SELECTED = CHECKBOX_SELECTED_INDICATOR
    common.INDICATOR_UNSELECTED = CHECKBOX_UNSELECTED_INDICATOR
    try:
        yield
    finally:
        constants.INDICATOR_SELECTED = old_selected
        constants.INDICATOR_UNSELECTED = old_unselected
        common.INDICATOR_SELECTED = old_common_selected
        common.INDICATOR_UNSELECTED = old_common_unselected


def ask_checkbox(message, choices, default_values=None, style=None, instruction=None):
    """Ask a checkbox question using questionary for multi-select."""
    normalized = [_normalize_choice(choice) for choice in choices]
    default_set = set(default_values or [])
    selectable = [choice for choice in normalized if not choice["separator"]]
    if not selectable:
        return []

    try:
        import questionary
    except ImportError:
        _render_heading("Checkbox", message)
        click.echo("Enter comma-separated numbers to keep selected items.", err=True)
        selected_indexes = [
            str(index)
            for index, choice in enumerate(selectable, start=1)
            if choice["checked"] or (choice["value"] in default_set)
        ]
        for index, choice in enumerate(selectable, start=1):
            marker = "x" if (choice["checked"] or (choice["value"] in default_set)) else " "
            click.echo(f"  {index}. [{marker}] {choice['title']}", err=True)
        raw_value = click.prompt(
            "Choice numbers",
            default=",".join(selected_indexes),
            show_default=bool(selected_indexes),
            prompt_suffix=": ",
            err=True,
        )
        selected = []
        for part in str(raw_value).split(","):
            item = part.strip()
            if not item or not item.isdigit():
                continue
            index = int(item)
            if 1 <= index <= len(selectable):
                selected.append(selectable[index - 1]["value"])
        return selected

    questionary_choices = []
    for choice in normalized:
        if choice["separator"]:
            questionary_choices.append(questionary.Separator())
            continue
        questionary_choices.append(
            questionary.Choice(
                title=choice["title"],
                value=choice["value"],
                checked=choice["checked"] or (choice["value"] in default_set),
            )
        )
    with checkbox_indicator_style():
        selected = questionary.checkbox(
            message,
            choices=questionary_choices,
            qmark="",
            pointer=">",
            style=style or _questionary_select_style(questionary),
            use_arrow_keys=True,
            use_jk_keys=True,
            instruction=instruction or "",
        ).ask()
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
