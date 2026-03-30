from contextlib import contextmanager


BACK_VALUE = "__BACK__"
CHECKBOX_SELECTED_INDICATOR = "☑"
CHECKBOX_UNSELECTED_INDICATOR = "☐"

def get_style():
    """Custom style for questionary."""
    import questionary
    return questionary.Style([
        ('qmark', 'fg:#5f819d bold'),       # token in front of the question
        ('question', 'bold'),               # question text
        ('answer', 'fg:#f44336 bold'),      # submitted answer text
        ('pointer', 'fg:#673ab7 bold'),     # pointer used in select and checkbox
        ('highlighted', 'fg:#673ab7 bold'), # highlighted option in select and checkbox
        ('selected', 'fg:#cc545a'),         # selected checkbox
        ('separator', 'fg:#cc545a'),        # separator in lists
        ('instruction', 'fg:#808080'),      # user instructions for select, rawselect, checkbox
        ('text', ''),                       # plain text
        ('disabled', 'fg:#858585 italic')   # disabled choices for select and checkbox
    ])

def ask_with_escape_back(question):
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.key_binding.key_bindings import merge_key_bindings
    from prompt_toolkit.keys import Keys
    
    bindings = KeyBindings()
    @bindings.add(Keys.Escape, eager=True)
    def _(_event):
        _event.app.exit(result=BACK_VALUE)
    try:
        question.application.key_bindings = merge_key_bindings([question.application.key_bindings, bindings])
    except Exception:
        pass
    return question.unsafe_ask()

def is_interactive_available():
    """Check if interactive mode is available (questionary installed and TTY)."""
    import sys
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return False
    try:
        import questionary
        return True
    except ImportError:
        return False

def get_separator():
    """Return a questionary Separator."""
    import questionary
    return questionary.Separator()

def create_choice(title, value, checked=False):
    """Return a questionary Choice."""
    import questionary
    return questionary.Choice(title=title, value=value, checked=checked)

def ask_select(message, choices, style=None):
    """Ask a selection question with escape back support."""
    import questionary
    if style is None:
        style = get_style()
    return ask_with_escape_back(questionary.select(
        message,
        choices=choices,
        style=style,
        use_arrow_keys=True
    ))


@contextmanager
def checkbox_indicator_style():
    """Temporarily render questionary checkboxes as checkbox glyphs."""
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


def ask_checkbox(message, choices, style=None, instruction=None):
    """Ask a checkbox question with shared style and escape back support."""
    import questionary
    if style is None:
        style = get_style()
    with checkbox_indicator_style():
        return ask_with_escape_back(questionary.checkbox(
            message,
            choices=choices,
            style=style,
            use_arrow_keys=True,
            instruction=instruction,
        ))

def ask_text(message, default="", password=False, style=None):
    """Ask a text question with escape back support."""
    import questionary
    if style is None:
        style = get_style()
    
    if password:
        q = questionary.password(message, style=style)
    else:
        q = questionary.text(message, default=default, style=style)
    return ask_with_escape_back(q)

def ask_path(message, default="", style=None):
    """Ask a path question with escape back support."""
    import questionary
    if style is None:
        style = get_style()
    return ask_with_escape_back(questionary.path(message, default=default, style=style))

def ask_confirm(message, default=True, style=None):
    """Ask a confirmation question."""
    import questionary
    if style is None:
        style = get_style()
    return ask_with_escape_back(questionary.confirm(message, default=default, style=style))
