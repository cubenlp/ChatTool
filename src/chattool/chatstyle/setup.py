"""Setup-stage display helpers."""

from __future__ import annotations

from collections.abc import Iterable

import click

from .output import _render_heading, _render_note


def setup_start(name: str) -> None:
    _render_heading("Setup", f"Start {name} setup")


def setup_stage(message: str) -> None:
    click.echo(message, err=True)


def setup_success(message: str) -> None:
    click.echo(message)


def setup_warning(message: str) -> None:
    click.echo(message, err=True)


def setup_failure(message: str) -> None:
    click.echo(message, err=True)


def setup_suggested_commands(commands: Iterable[str], *, heading: str | None = None) -> None:
    """Print commands users should run manually when setup cannot execute them."""

    if heading:
        _render_heading("Suggested Commands", heading)
    else:
        _render_heading("Suggested Commands")
    for command in commands:
        click.echo(command)


def setup_config_priority(items: Iterable[str]) -> None:
    _render_note("Config priority: " + " > ".join(items))


__all__ = [
    "setup_config_priority",
    "setup_failure",
    "setup_stage",
    "setup_start",
    "setup_success",
    "setup_suggested_commands",
    "setup_warning",
]
