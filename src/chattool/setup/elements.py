from dataclasses import dataclass, field
from typing import Callable, Sequence
import click

from chattool.setup.chrome import setup_chrome_driver
from chattool.setup.claude import setup_claude
from chattool.setup.codex import setup_codex
from chattool.setup.frp import setup_frp
from chattool.setup.alias import setup_alias
from chattool.setup.nodejs import setup_nodejs


@dataclass(frozen=True)
class SetupOptionElement:
    param_decls: Sequence[str]
    kwargs: dict = field(default_factory=dict)


@dataclass(frozen=True)
class SetupCommandElement:
    name: str
    help: str
    callback: Callable
    options: Sequence[SetupOptionElement] = field(default_factory=tuple)


def chrome_setup(interactive):
    setup_chrome_driver(interactive=interactive)


def frp_setup(interactive):
    setup_frp(interactive=interactive)


def nodejs_setup(interactive):
    setup_nodejs(interactive=interactive)


def alias_setup(shell, dry_run):
    setup_alias(shell=shell, dry_run=dry_run)


def codex_setup(preferred_auth_method, base_url, model, interactive):
    setup_codex(
        preferred_auth_method=preferred_auth_method,
        base_url=base_url,
        model=model,
        interactive=interactive,
    )


def claude_setup(auth_token, base_url, small_fast_model, interactive):
    setup_claude(
        auth_token=auth_token,
        base_url=base_url,
        small_fast_model=small_fast_model,
        interactive=interactive,
    )


SETUP_COMMAND_ELEMENTS = (
    SetupCommandElement(
        name="alias",
        help="Setup shell aliases for ChatTool commands.",
        callback=alias_setup,
        options=(
            SetupOptionElement(
                param_decls=("-s", "--shell"),
                kwargs={"default": None, "type": click.Choice(["zsh", "bash"]), "help": "Target shell: zsh or bash. Defaults to $SHELL."},
            ),
            SetupOptionElement(
                param_decls=("--dry-run",),
                kwargs={"is_flag": True, "help": "Preview alias changes without writing to shell rc file."},
            ),
        ),
    ),
    SetupCommandElement(
        name="claude",
        help="Setup Claude Code CLI and config files.",
        callback=claude_setup,
        options=(
            SetupOptionElement(
                param_decls=("--interactive/--no-interactive", "-i/-I"),
                kwargs={"default": None, "help": "Auto prompt on missing args, -i forces interactive, -I disables it."},
            ),
            SetupOptionElement(
                param_decls=("--auth-token", "--token"),
                kwargs={"default": None, "help": "Value for ANTHROPIC_AUTH_TOKEN."},
            ),
            SetupOptionElement(
                param_decls=("--base-url", "--url"),
                kwargs={"default": None, "help": "Optional ANTHROPIC_BASE_URL value."},
            ),
            SetupOptionElement(
                param_decls=("--small-fast-model", "--sfm"),
                kwargs={"default": None, "help": "Optional ANTHROPIC_SMALL_FAST_MODEL value."},
            ),
        ),
    ),
    SetupCommandElement(
        name="chrome",
        help="Setup Chrome and Chromedriver.",
        callback=chrome_setup,
        options=(
            SetupOptionElement(
                param_decls=("--interactive/--no-interactive", "-i/-I"),
                kwargs={"default": None, "help": "Auto prompt on missing args, -i forces interactive, -I disables it."},
            ),
        ),
    ),
    SetupCommandElement(
        name="frp",
        help="Setup FRP Client/Server.",
        callback=frp_setup,
        options=(
            SetupOptionElement(
                param_decls=("--interactive/--no-interactive", "-i/-I"),
                kwargs={"default": None, "help": "Auto prompt on missing args, -i forces interactive, -I disables it."},
            ),
        ),
    ),
    SetupCommandElement(
        name="nodejs",
        help="Setup nvm and Node.js (default LTS).",
        callback=nodejs_setup,
        options=(
            SetupOptionElement(
                param_decls=("--interactive/--no-interactive", "-i/-I"),
                kwargs={"default": None, "help": "Auto prompt on missing args, -i forces interactive, -I disables it."},
            ),
        ),
    ),
    SetupCommandElement(
        name="codex",
        help="Setup Codex CLI and config files.",
        callback=codex_setup,
        options=(
            SetupOptionElement(
                param_decls=("--interactive/--no-interactive", "-i/-I"),
                kwargs={"default": None, "help": "Auto prompt on missing args, -i forces interactive, -I disables it."},
            ),
            SetupOptionElement(
                param_decls=("--preferred-auth-method", "--pam"),
                kwargs={"default": None, "help": "Value for preferred_auth_method and OPENAI_API_KEY."},
            ),
            SetupOptionElement(
                param_decls=("--base-url", "--url"),
                kwargs={"default": None, "help": "Optional base_url for model provider."},
            ),
            SetupOptionElement(
                param_decls=("--model",),
                kwargs={"default": None, "help": "Optional default model name."},
            ),
        ),
    ),
)
