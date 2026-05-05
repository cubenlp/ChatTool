"""Compatibility shim for prompt primitives."""

from chattool.chatstyle.prompt import (
    ask_checkbox,
    ask_checkbox_with_controls,
    ask_confirm,
    ask_path,
    ask_select,
    ask_text,
    checkbox_indicator_style,
    get_style,
    is_interactive_available,
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
