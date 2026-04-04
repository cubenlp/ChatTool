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
    return questionary.Style(
        [
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
        ]
    )


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
            marker = (
                "x" if (choice["checked"] or (choice["value"] in default_set)) else " "
            )
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


def ask_checkbox_with_controls(
    message,
    choices,
    default_values=None,
    style=None,
    instruction=None,
    select_all_label="Select all",
):
    """Ask for checkbox selections with a live select-all control item."""
    normalized = [_normalize_choice(choice) for choice in choices]
    selectable = [choice for choice in normalized if not choice["separator"]]
    if not selectable:
        return []

    default_set = set(default_values or [])
    initial_values = [
        choice["value"]
        for choice in selectable
        if choice["checked"] or (choice["value"] in default_set)
    ]

    control_value = "__all__"
    inline_choices = [
        create_choice(
            title=select_all_label,
            value=control_value,
            checked=len(initial_values) == len(selectable),
        ),
        get_separator(),
        *choices,
    ]

    try:
        from prompt_toolkit.application import Application
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.keys import Keys
        from prompt_toolkit.styles import Style

        from questionary import utils
        from questionary.constants import DEFAULT_QUESTION_PREFIX
        from questionary.constants import DEFAULT_SELECTED_POINTER
        from questionary.prompts import common
        from questionary.prompts.common import InquirerControl
        from questionary.prompts.common import Separator
        from questionary.question import Question
        from questionary.styles import merge_styles_default
    except ImportError:
        selected = ask_checkbox(
            message,
            choices=inline_choices,
            default_values=initial_values,
            style=style,
            instruction=instruction,
        )
        if selected == BACK_VALUE:
            return BACK_VALUE
        filtered = [value for value in selected if value != control_value]
        if control_value in selected:
            if len(filtered) == len(selectable):
                return []
            return [choice["value"] for choice in selectable]
        return filtered

    merged_style = merge_styles_default(
        [Style([("bottom-toolbar", "noreverse")]), style]
    )
    questionary_choices = [
        create_choice(
            title=select_all_label,
            value=control_value,
            checked=len(initial_values) == len(selectable),
        ),
        Separator(),
        *choices,
    ]

    class CheckboxControl(InquirerControl):
        def _get_choice_tokens(self):
            tokens = []

            def append(index, choice):
                selected = choice.value in self.selected_options

                if index == self.pointed_at:
                    if self.pointer is not None:
                        tokens.append(("class:pointer", f" {self.pointer} "))
                    else:
                        tokens.append(("class:text", " " * 3))
                    tokens.append(("[SetCursorPosition]", ""))
                else:
                    pointer_length = (
                        len(self.pointer) if self.pointer is not None else 1
                    )
                    tokens.append(("class:text", " " * (2 + pointer_length)))

                if isinstance(choice, Separator):
                    tokens.append(("class:separator", f"{choice.title}"))
                    tokens.append(("", "\n"))
                    return

                indicator = (
                    CHECKBOX_SELECTED_INDICATOR
                    if selected
                    else CHECKBOX_UNSELECTED_INDICATOR
                )
                tokens.append(("class:text", f"{indicator} "))
                title = (
                    choice.title
                    if isinstance(choice.title, str)
                    else choice.title[0][1]
                )
                tokens.append(("class:text", f"{title}"))
                tokens.append(("", "\n"))

            for i, c in enumerate(self.filtered_choices):
                append(i, c)

            if tokens:
                tokens.pop()
            return tokens

    ic = CheckboxControl(
        questionary_choices,
        None,
        pointer=DEFAULT_SELECTED_POINTER,
        initial_choice=None,
        show_description=True,
    )

    regular_values = [choice["value"] for choice in selectable]
    ic.selected_options = list(initial_values)

    def _sync_select_all() -> None:
        all_selected = all(value in ic.selected_options for value in regular_values)
        if all_selected:
            if control_value not in ic.selected_options:
                ic.selected_options.append(control_value)
        elif control_value in ic.selected_options:
            ic.selected_options.remove(control_value)

    _sync_select_all()

    def get_selected_values():
        return [value for value in ic.selected_options if value != control_value]

    def perform_validation(selected_values):
        ic.error_message = None
        return True

    def get_prompt_tokens():
        tokens = []
        tokens.append(("class:qmark", DEFAULT_QUESTION_PREFIX))
        tokens.append(("class:question", f" {message}"))
        if ic.is_answered:
            nbr_selected = len(get_selected_values())
            if nbr_selected == 0:
                tokens.append(("class:answer", "done"))
            elif nbr_selected == 1:
                current = next(
                    choice
                    for choice in selectable
                    if choice["value"] == get_selected_values()[0]
                )
                tokens.append(("class:answer", f"[{current['title']}]"))
            else:
                tokens.append(("class:answer", f"done ({nbr_selected} selections)"))
        else:
            tokens.append(("class:instruction", instruction or ""))
        return tokens

    layout = common.create_inquirer_layout(ic, get_prompt_tokens)
    bindings = KeyBindings()

    @bindings.add(Keys.ControlQ, eager=True)
    @bindings.add(Keys.ControlC, eager=True)
    def _(event):
        event.app.exit(exception=KeyboardInterrupt, style="class:aborting")

    @bindings.add(" ", eager=True)
    def toggle(_event):
        pointed_choice = ic.get_pointed_at().value
        if pointed_choice == control_value:
            if all(value in ic.selected_options for value in regular_values):
                ic.selected_options = [
                    value
                    for value in ic.selected_options
                    if value not in regular_values and value != control_value
                ]
            else:
                ic.selected_options = list(
                    dict.fromkeys([*regular_values, control_value])
                )
        else:
            if pointed_choice in ic.selected_options:
                ic.selected_options.remove(pointed_choice)
            else:
                ic.selected_options.append(pointed_choice)
            _sync_select_all()

        perform_validation(get_selected_values())

    @bindings.add("i", eager=True)
    def invert(_event):
        inverted_selection = [
            c.value
            for c in ic.choices
            if not isinstance(c, Separator)
            and c.value != control_value
            and c.value not in ic.selected_options
            and not c.disabled
        ]
        ic.selected_options = inverted_selection
        _sync_select_all()
        perform_validation(get_selected_values())

    @bindings.add("a", eager=True)
    def all_toggle(_event):
        if all(value in ic.selected_options for value in regular_values):
            ic.selected_options = []
        else:
            ic.selected_options = list(regular_values)
        _sync_select_all()
        perform_validation(get_selected_values())

    def move_cursor_down(event):
        ic.select_next()
        while not ic.is_selection_valid():
            ic.select_next()

    def move_cursor_up(event):
        ic.select_previous()
        while not ic.is_selection_valid():
            ic.select_previous()

    bindings.add(Keys.Down, eager=True)(move_cursor_down)
    bindings.add(Keys.Up, eager=True)(move_cursor_up)
    bindings.add("j", eager=True)(move_cursor_down)
    bindings.add("k", eager=True)(move_cursor_up)
    bindings.add(Keys.ControlN, eager=True)(move_cursor_down)
    bindings.add(Keys.ControlP, eager=True)(move_cursor_up)

    @bindings.add(Keys.ControlM, eager=True)
    def set_answer(event):
        selected_values = get_selected_values()
        ic.submission_attempted = True
        if perform_validation(selected_values):
            ic.is_answered = True
            event.app.exit(result=selected_values)

    @bindings.add(Keys.Any)
    def other(_event):
        """Disallow inserting other text."""

    with checkbox_indicator_style():
        question = Question(
            Application(
                layout=layout,
                key_bindings=bindings,
                style=merged_style,
                **utils.used_kwargs({}, Application.__init__),
            )
        )
        selected = question.ask()
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
