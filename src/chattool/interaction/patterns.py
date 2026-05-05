"""Reusable interaction patterns for CLI commands."""

from __future__ import annotations

from typing import Any

from chattool.chatstyle.mask import prompt_sensitive_value
from chattool.chatstyle.prompt import ask_text


def resolve_value(*candidates: Any) -> Any:
    """Return the first usable value from the provided candidates.

    `None` and blank strings are treated as missing values.
    `False` and `0` are preserved as valid values.
    """

    for candidate in candidates:
        if candidate is None:
            continue
        if isinstance(candidate, str) and not candidate.strip():
            continue
        return candidate
    return None


def prompt_text_value(
    label: str,
    *candidates: Any,
    fallback: str = "",
) -> str:
    """Prompt for a text value using the resolved default candidate."""

    default_value = resolve_value(*candidates)
    if default_value is None:
        default_value = fallback
    return ask_text(label, default=str(default_value))


__all__ = [
    "prompt_sensitive_value",
    "prompt_text_value",
    "resolve_value",
]
