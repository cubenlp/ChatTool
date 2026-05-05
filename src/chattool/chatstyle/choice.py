"""Compatibility choice helpers delegated to external :mod:`chatstyle`."""

from chatstyle.tui.choice import (
    _normalize_choice,
    _questionary_select_style,
    create_choice,
    get_separator,
)


__all__ = ["create_choice", "get_separator"]
