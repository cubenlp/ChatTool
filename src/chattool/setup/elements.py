from dataclasses import dataclass, field
from typing import Callable, Sequence

from chattool.setup.chrome import setup_chrome_driver
from chattool.setup.codex import setup_codex
from chattool.setup.frp import setup_frp
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


def frp_setup():
    setup_frp()


def nodejs_setup(interactive):
    setup_nodejs(interactive=interactive)


def codex_setup(preferred_auth_method, interactive):
    setup_codex(preferred_auth_method=preferred_auth_method, interactive=interactive)


SETUP_COMMAND_ELEMENTS = (
    SetupCommandElement(
        name="chrome",
        help="Setup Chrome and Chromedriver.",
        callback=chrome_setup,
        options=(
            SetupOptionElement(
                param_decls=("--interactive", "-i"),
                kwargs={"is_flag": True, "help": "Interactive mode to choose install directory."},
            ),
        ),
    ),
    SetupCommandElement(
        name="frp",
        help="Setup FRP Client/Server.",
        callback=frp_setup,
    ),
    SetupCommandElement(
        name="nodejs",
        help="Setup nvm and Node.js (default LTS).",
        callback=nodejs_setup,
        options=(
            SetupOptionElement(
                param_decls=("--interactive", "-i"),
                kwargs={"is_flag": True, "help": "Interactive mode to choose Node.js version."},
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
        ),
    ),
)
