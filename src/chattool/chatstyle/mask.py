"""Sensitive value masking and prompt helpers."""

from __future__ import annotations

from typing import Callable

from .prompt import ask_text


def mask_secret(value: str | None) -> str:
    """Mask a secret while preserving the historical ChatTool shape."""

    if not value:
        return ""

    length = len(value)
    if length <= 2:
        return "*" * length
    if length <= 6:
        return value[0] + "*" * (length - 2) + value[-1]
    if length <= 14:
        return value[:2] + "*" * (length - 4) + value[-2:]
    if length <= 30:
        return value[:4] + "*" * (length - 8) + value[-4:]
    return value[:8] + "*" * (length - 12) + value[-8:]


def format_current_secret(value: str | None, mask_fn: Callable[[str], str] | None = None) -> str:
    """Return the common current-value hint for sensitive prompts."""

    if not value:
        return ""
    masker = mask_fn or mask_secret
    return f"current: {masker(value)}"


def prompt_sensitive_value(
    label: str,
    current_value: str | None,
    mask_fn: Callable[[str], str] | None = None,
) -> str | None:
    """Prompt for a secret while allowing Enter to keep the existing value."""

    prompt_label = label
    current_hint = format_current_secret(current_value, mask_fn)
    if current_hint:
        prompt_label = f"{label} ({current_hint}, enter to keep)"
    entered = ask_text(prompt_label, password=True)
    if entered:
        return entered
    return current_value


__all__ = ["format_current_secret", "mask_secret", "prompt_sensitive_value"]
