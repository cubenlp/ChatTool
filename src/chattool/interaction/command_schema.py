"""ChatTool policy adapter for external :mod:`chatstyle` command schemas."""

from chatstyle import (
    CommandConstraint,
    CommandField,
    CommandSchema,
    InteractiveResolution,
    add_interactive_option,
)
from chatstyle import resolve_command_inputs as _resolve_command_inputs
from chatstyle.tui.prompt import ask_confirm, ask_path, ask_select, ask_text

from .policy import resolve_interactive_mode


def resolve_command_inputs(*, schema, provided, interactive, usage):
    """Resolve command inputs through ChatStyle while preserving old patch points."""

    return _resolve_command_inputs(
        schema=schema,
        provided=provided,
        interactive=interactive,
        usage=usage,
        prompt_runtime_override=_PromptRuntime,
        interactive_resolver_override=_resolve_interactive_for_chatstyle,
    )


class _PromptRuntime:
    ask_confirm = staticmethod(lambda *args, **kwargs: ask_confirm(*args, **kwargs))
    ask_path = staticmethod(lambda *args, **kwargs: ask_path(*args, **kwargs))
    ask_select = staticmethod(lambda *args, **kwargs: ask_select(*args, **kwargs))
    ask_text = staticmethod(lambda *args, **kwargs: ask_text(*args, **kwargs))


def _resolve_interactive_for_chatstyle(*, interactive, auto_prompt_condition):
    (
        normalized,
        can_prompt,
        force_interactive,
        _auto_interactive,
        need_prompt,
    ) = resolve_interactive_mode(interactive, auto_prompt_condition)
    return InteractiveResolution(
        interactive=normalized,
        can_prompt=can_prompt,
        force_interactive=force_interactive,
        need_prompt=need_prompt,
    )

__all__ = [
    "CommandConstraint",
    "CommandField",
    "CommandSchema",
    "InteractiveResolution",
    "add_interactive_option",
    "ask_confirm",
    "ask_path",
    "ask_select",
    "ask_text",
    "resolve_command_inputs",
]
