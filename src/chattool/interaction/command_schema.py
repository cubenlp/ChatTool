"""Declarative command input resolution for interactive CLI commands."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Sequence

import click

from .policy import abort_if_force_without_tty, resolve_interactive_mode
from .prompt import ask_confirm, ask_path, ask_select, ask_text


ValueValidator = Callable[[Any, dict[str, Any]], str | None]
ConstraintValidator = Callable[[dict[str, Any]], str | None]


def add_interactive_option(func):
    """Attach the shared interactive option to a Click command."""
    return click.option(
        "--interactive/--no-interactive",
        "interactive",
        "-i/-I",
        default=None,
        help="Auto prompt on missing args, -i forces interactive, -I disables it.",
    )(func)


@dataclass(frozen=True)
class CommandField:
    name: str
    prompt: str
    kind: str = "text"
    required: bool = False
    default: Any = None
    default_factory: Callable[[], Any] | None = None
    choices: Sequence[str] = ()
    sensitive: bool = False
    prompt_if_missing: bool = False
    normalizer: Callable[[Any], Any] | None = None
    validator: ValueValidator | None = None
    missing_message: str | None = None

    def resolve_default(self):
        if self.default_factory is not None:
            return self.default_factory()
        return self.default


@dataclass(frozen=True)
class CommandConstraint:
    validator: ConstraintValidator
    message: str = ""


@dataclass(frozen=True)
class CommandSchema:
    name: str
    fields: Sequence[CommandField] = field(default_factory=tuple)
    constraints: Sequence[CommandConstraint] = field(default_factory=tuple)


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == () or value == []


def _normalize_field_value(field: CommandField, value: Any):
    if _is_empty(value):
        return value
    if field.kind == "int" and not isinstance(value, int):
        value = int(value)
    if field.kind == "float" and not isinstance(value, float):
        value = float(value)
    if field.normalizer is not None:
        value = field.normalizer(value)
    return value


def _prompt_for_field(field: CommandField, current: Any):
    default = current if not _is_empty(current) else field.resolve_default()
    if field.kind == "select":
        if not field.choices:
            raise click.ClickException(f"Field '{field.name}' is missing choices.")
        return ask_select(field.prompt, list(field.choices))
    if field.kind == "confirm":
        return ask_confirm(
            field.prompt, default=bool(default) if default is not None else True
        )
    if field.kind == "path":
        return ask_path(field.prompt, default=str(default or ""))
    return ask_text(field.prompt, default=str(default or ""), password=field.sensitive)


def _collect_errors(schema: CommandSchema, values: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in schema.fields:
        value = values.get(field.name)
        if field.required and _is_empty(value):
            errors.append(
                field.missing_message or f"Missing required value: {field.name}"
            )
            continue
        if field.validator is None or _is_empty(value):
            continue
        message = field.validator(value, values)
        if message:
            errors.append(message)

    for constraint in schema.constraints:
        message = constraint.validator(values)
        if message:
            errors.append(constraint.message or message)
    return errors


def resolve_command_inputs(
    *,
    schema: CommandSchema,
    provided: dict[str, Any],
    interactive: bool | None,
    usage: str,
) -> dict[str, Any]:
    values: dict[str, Any] = {}
    missing_before_defaults: set[str] = set()
    for field in schema.fields:
        raw = provided.get(field.name)
        if _is_empty(raw):
            missing_before_defaults.add(field.name)
        if _is_empty(raw):
            raw = field.resolve_default()
        values[field.name] = _normalize_field_value(field, raw)

    promptable_missing = [
        field
        for field in schema.fields
        if (
            _is_empty(values.get(field.name))
            and (field.required or field.prompt_if_missing)
        )
        or (field.prompt_if_missing and field.name in missing_before_defaults)
    ]
    initial_errors = _collect_errors(schema, values)

    interactive, can_prompt, force_interactive, _, need_prompt = (
        resolve_interactive_mode(
            interactive=interactive,
            auto_prompt_condition=bool(promptable_missing or initial_errors),
        )
    )
    abort_if_force_without_tty(force_interactive, can_prompt, usage)

    if (promptable_missing or initial_errors) and interactive is False:
        raise click.ClickException(initial_errors[0] if initial_errors else usage)
    if (
        (promptable_missing or initial_errors)
        and interactive is None
        and not can_prompt
    ):
        message = initial_errors[0] if initial_errors else "Missing required values."
        raise click.ClickException(f"{message}\n{usage}")

    if need_prompt:
        for field in schema.fields:
            current = values.get(field.name)
            should_prompt = field.required and _is_empty(current)
            should_prompt = should_prompt or (
                field.prompt_if_missing and field.name in missing_before_defaults
            )
            if not should_prompt:
                continue
            prompted = _prompt_for_field(field, current)
            values[field.name] = _normalize_field_value(field, prompted)

    final_errors = _collect_errors(schema, values)
    if final_errors:
        raise click.ClickException(final_errors[0])
    return values


__all__ = [
    "CommandConstraint",
    "CommandField",
    "CommandSchema",
    "add_interactive_option",
    "resolve_command_inputs",
]
