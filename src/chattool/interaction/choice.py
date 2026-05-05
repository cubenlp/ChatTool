"""Compatibility shim for choice helpers."""

from chattool.chatstyle.choice import (
    _normalize_choice,
    _questionary_select_style,
    create_choice,
    get_separator,
)

__all__ = [
    "_normalize_choice",
    "_questionary_select_style",
    "create_choice",
    "get_separator",
]
