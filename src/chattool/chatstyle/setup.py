"""Compatibility setup-stage helpers backed by external :mod:`chatstyle` flow."""

from chatstyle import (
    render_config_priority,
    render_failure,
    render_flow_start,
    render_stage,
    render_success,
    render_suggested_commands,
    render_warning,
)

def setup_start(name: str) -> None:
    render_flow_start(name, title="Setup")


def setup_stage(message: str) -> None:
    render_stage(message)


def setup_success(message: str) -> None:
    render_success(message)


def setup_warning(message: str) -> None:
    render_warning(message)


def setup_failure(message: str) -> None:
    render_failure(message)


def setup_suggested_commands(commands, *, heading: str | None = None) -> None:
    """Print commands users should run manually when setup cannot execute them."""

    render_suggested_commands(commands, description=heading)


def setup_config_priority(items) -> None:
    render_config_priority(items)


__all__ = [
    "setup_config_priority",
    "setup_failure",
    "setup_stage",
    "setup_start",
    "setup_success",
    "setup_suggested_commands",
    "setup_warning",
]
