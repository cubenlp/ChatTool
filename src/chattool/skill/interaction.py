from __future__ import annotations

import click

from chattool.interaction import (
    BACK_VALUE,
    ask_checkbox_with_controls,
    ask_select,
    create_choice,
)


def prompt_install_targets(available: list[str]) -> list[str] | str:
    choices = [
        create_choice(title=skill_name, value=skill_name) for skill_name in available
    ]
    selected = ask_checkbox_with_controls(
        "Select skills to install",
        choices=choices,
        default_values=available,
        instruction="(Use arrow keys to move, <space> to toggle, <a> to toggle all, <enter> to confirm)",
        select_all_label="Select all skills",
    )
    if selected == BACK_VALUE:
        return BACK_VALUE
    return list(selected)


def prompt_platform() -> str:
    choices = [
        create_choice(title="codex", value="codex"),
        create_choice(title="claude", value="claude"),
        create_choice(title="opencode", value="opencode"),
    ]
    selected = ask_select("Select a platform (default: codex):", choices=choices)
    if selected == BACK_VALUE:
        raise click.Abort()
    return str(selected)


def prompt_overwrite_action(skill_name: str) -> str:
    while True:
        answer = click.prompt(
            f"Skill already exists: {skill_name}. Overwrite? [y/N/a]",
            default="",
            show_default=False,
            prompt_suffix=" ",
            err=True,
        )
        normalized = answer.strip().lower()
        if normalized in {"", "n", "no"}:
            return "skip"
        if normalized in {"y", "yes"}:
            return "overwrite"
        if normalized == "a":
            return "all"
        click.echo("Please enter y, n, or a.", err=True)
