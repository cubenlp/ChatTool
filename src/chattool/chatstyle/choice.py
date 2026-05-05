"""Choice helpers shared by select and checkbox prompts."""


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


__all__ = ["create_choice", "get_separator"]
