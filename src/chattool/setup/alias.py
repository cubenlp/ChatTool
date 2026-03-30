import os
from pathlib import Path

import click

from chattool.utils.custom_logger import setup_logger
from chattool.utils.tui import BACK_VALUE, ask_checkbox, ask_select, create_choice, is_interactive_available

logger = setup_logger("setup_alias")

ALIAS_MAP = {
    "chatenv": "chattool env",
    "chatskill": "chattool skill",
    "chatdns": "chattool dns",
    "chatgh": "chattool gh",
    "chatcc": "chattool cc",
    "chatcli": "chattool client",
    "chatpypi": "chattool pypi",
    "chatup": "chattool setup",
    "chatlark": "chattool lark",
    "chatimg": "chattool image",
    "chatnet": "chattool network",
}

BLOCK_BEGIN = "# >>> chattool aliases >>>"
BLOCK_END = "# <<< chattool aliases <<<"


def resolve_shell(shell=None):
    if shell in {"zsh", "bash"}:
        return shell
    shell_env = os.path.basename(os.environ.get("SHELL", "")).lower()
    if "zsh" in shell_env:
        return "zsh"
    if "bash" in shell_env:
        return "bash"
    return "bash"


def resolve_shell_rc(shell, home=None):
    home_path = Path(home) if home else Path.home()
    if shell == "zsh":
        return home_path / ".zshrc"
    if shell == "bash":
        return home_path / ".bashrc"
    raise ValueError(f"Unsupported shell: {shell}")


def render_alias_block(alias_keys):
    if not alias_keys:
        return ""
    lines = [BLOCK_BEGIN]
    for key in alias_keys:
        lines.append(f"alias {key}='{ALIAS_MAP[key]}'")
    lines.append(BLOCK_END)
    return "\n".join(lines) + "\n"


def apply_alias_block(rc_path, block):
    content = ""
    if rc_path.exists():
        content = rc_path.read_text(encoding="utf-8")
    begin_idx = content.find(BLOCK_BEGIN)
    end_idx = content.find(BLOCK_END)
    if begin_idx != -1 and end_idx != -1 and end_idx >= begin_idx:
        end_idx = end_idx + len(BLOCK_END)
        if end_idx < len(content) and content[end_idx:end_idx + 1] == "\n":
            end_idx += 1
        content = content[:begin_idx] + content[end_idx:]
    content = content.rstrip("\n")
    if block:
        if content:
            content = content + "\n\n" + block.rstrip("\n")
        else:
            content = block.rstrip("\n")
    rc_path.parent.mkdir(parents=True, exist_ok=True)
    rc_path.write_text(content + ("\n" if content else ""), encoding="utf-8")


def select_aliases_interactively(default_selected):
    preset = ask_select(
        "Alias preset",
        choices=["Select all", "Unselect all", "Custom"],
    )
    if preset == BACK_VALUE:
        return BACK_VALUE
    if preset == "Select all":
        return list(ALIAS_MAP.keys())
    if preset == "Unselect all":
        return []

    choices = [
        create_choice(
            title=f"{name} => {cmd}",
            value=name,
            checked=name in default_selected,
        )
        for name, cmd in ALIAS_MAP.items()
    ]
    selected = ask_checkbox(
        "Select aliases (Space to toggle, A select/unselect all)",
        choices=choices,
        instruction="",
    )
    if selected == BACK_VALUE:
        return BACK_VALUE
    return selected or []


def setup_alias(shell=None, dry_run=False):
    if os.name != "posix":
        click.echo("setup alias only supports Unix-like systems.", err=True)
        raise click.Abort()
    shell_name = resolve_shell(shell)
    rc_path = resolve_shell_rc(shell_name)
    logger.info(f"Start setup alias for shell: {shell_name}")

    default_selected = list(ALIAS_MAP.keys())
    if is_interactive_available():
        alias_keys = select_aliases_interactively(default_selected)
        if alias_keys == BACK_VALUE:
            raise click.Abort()
    else:
        alias_keys = default_selected
        click.echo("No interactive TTY detected, apply default alias set.")

    block = render_alias_block(alias_keys)
    if dry_run:
        click.echo(f"[dry-run] target shell rc: {rc_path}")
        if block:
            click.echo("[dry-run] alias block:")
            click.echo(block.rstrip("\n"))
            for key in alias_keys:
                click.echo(f"  {key} => {ALIAS_MAP[key]}")
        else:
            click.echo("[dry-run] alias block would be removed.")
        return

    apply_alias_block(rc_path, block)

    if alias_keys:
        click.echo(f"Updated aliases in {rc_path}")
        for key in alias_keys:
            click.echo(f"  {key} => {ALIAS_MAP[key]}")
    else:
        click.echo(f"Removed ChatTool alias block from {rc_path}")
    click.echo(f"Run: source {rc_path}")
