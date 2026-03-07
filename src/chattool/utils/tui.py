BACK_VALUE = "__BACK__"

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
