"""Compatibility prompt primitives delegated to external :mod:`chatstyle`."""

from chatstyle import get_style, is_interactive_available
from chatstyle.tui.prompt import (
    ask_checkbox,
    ask_checkbox_with_controls,
    ask_confirm,
    ask_path,
    ask_select,
    ask_text,
    checkbox_indicator_style,
)

__all__ = [
    "ask_checkbox",
    "ask_checkbox_with_controls",
    "ask_confirm",
    "ask_path",
    "ask_select",
    "ask_text",
    "checkbox_indicator_style",
    "get_style",
    "is_interactive_available",
]
