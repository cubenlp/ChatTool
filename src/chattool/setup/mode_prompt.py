from __future__ import annotations

from chattool.interaction import BACK_VALUE, ask_confirm


def resolve_install_only_mode(*, need_prompt: bool, install_only: bool, can_prompt: bool):
    """Return the final install_only flag after the shared setup mode prompt.

    The prompt is only shown when the command is already in an interactive flow,
    install_only was not explicitly requested, and TTY prompting is available.
    """

    if not need_prompt or install_only or not can_prompt:
        return install_only, False

    should_configure = ask_confirm("Also write/update config files?", default=True)
    if should_configure == BACK_VALUE:
        return install_only, True
    return (not should_configure), False


__all__ = ["resolve_install_only_mode"]
