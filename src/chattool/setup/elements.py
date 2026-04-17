from dataclasses import dataclass, field
from typing import Callable, Sequence
import click

from chattool.setup.chrome import setup_chrome_driver
from chattool.setup.claude import setup_claude
from chattool.setup.codex import setup_codex
from chattool.setup.cc_connect import setup_cc_connect
from chattool.setup.docker import setup_docker
from chattool.setup.frp import setup_frp
from chattool.setup.lark_cli import setup_lark_cli
from chattool.setup.opencode import setup_opencode
from chattool.setup.alias import setup_alias
from chattool.setup.nodejs import setup_nodejs
from chattool.setup.workspace import setup_workspace


@dataclass(frozen=True)
class SetupOptionElement:
    param_decls: Sequence[str]
    kwargs: dict = field(default_factory=dict)

    @property
    def is_argument(self) -> bool:
        return all(not str(decl).startswith("-") for decl in self.param_decls)


@dataclass(frozen=True)
class SetupCommandElement:
    name: str
    help: str
    callback: Callable
    options: Sequence[SetupOptionElement] = field(default_factory=tuple)


def chrome_setup(update, interactive):
    setup_chrome_driver(interactive=interactive, update=update)


def frp_setup(interactive):
    setup_frp(interactive=interactive)


def nodejs_setup(interactive, log_level):
    setup_nodejs(interactive=interactive, log_level=log_level)


def docker_setup(sudo, interactive, log_level):
    setup_docker(interactive=interactive, use_sudo=sudo, log_level=log_level)


def alias_setup(shell, dry_run):
    setup_alias(shell=shell, dry_run=dry_run)


def codex_setup(api_key, base_url, model, env, interactive, install_only, log_level):
    setup_codex(
        api_key=api_key,
        base_url=base_url,
        model=model,
        env_ref=env,
        interactive=interactive,
        install_only=install_only,
        log_level=log_level,
    )


def cc_connect_setup(sudo=None, interactive=None, log_level="INFO"):
    setup_cc_connect(interactive=interactive, log_level=log_level)


def claude_setup(auth_token, base_url, small_fast_model, interactive, install_only, log_level):
    setup_claude(
        auth_token=auth_token,
        base_url=base_url,
        small_fast_model=small_fast_model,
        interactive=interactive,
        install_only=install_only,
        log_level=log_level,
    )


def opencode_setup(
    base_url=None,
    api_key=None,
    model=None,
    env=None,
    interactive=None,
    plugin=None,
    install_only=False,
    log_level="INFO",
):
    setup_opencode(
        base_url=base_url,
        api_key=api_key,
        model=model,
        env_ref=env,
        interactive=interactive,
        plugin=plugin,
        install_only=install_only,
        log_level=log_level,
    )


def lark_cli_setup(app_id, app_secret, brand, env, interactive, log_level):
    setup_lark_cli(
        app_id=app_id,
        app_secret=app_secret,
        brand=brand,
        env_ref=env,
        interactive=interactive,
        log_level=log_level,
    )


LOG_LEVEL_OPTION = SetupOptionElement(
    param_decls=("-l", "--log-level"),
    kwargs={
        "default": "INFO",
        "show_default": True,
        "type": click.Choice(
            ["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False
        ),
        "help": "Console log level for staged setup logs.",
    },
)


def workspace_setup(
    profile,
    workspace_dir,
    language,
    interactive,
    force,
    dry_run,
    with_chattool,
    chattool_source,
    with_opencode_loop,
):
    setup_workspace(
        profile_name=profile,
        workspace_dir=workspace_dir,
        language=language,
        interactive=interactive,
        force=force,
        dry_run=dry_run,
        with_chattool=with_chattool,
        chattool_source=chattool_source,
        with_opencode_loop=with_opencode_loop,
    )


SETUP_COMMAND_ELEMENTS = (
    SetupCommandElement(
        name="alias",
        help="Setup shell aliases for ChatTool commands.",
        callback=alias_setup,
        options=(
            SetupOptionElement(
                param_decls=("-s", "--shell"),
                kwargs={
                    "default": None,
                    "type": click.Choice(["zsh", "bash"]),
                    "help": "Target shell override: zsh or bash. By default, update all detected shells.",
                },
            ),
            SetupOptionElement(
                param_decls=("--dry-run",),
                kwargs={
                    "is_flag": True,
                    "help": "Preview alias changes without writing to shell rc file.",
                },
            ),
        ),
    ),
    SetupCommandElement(
        name="cc-connect",
        help="Setup cc-connect CLI and runtime dependencies.",
        callback=cc_connect_setup,
        options=(
            LOG_LEVEL_OPTION,
            SetupOptionElement(
                param_decls=("--sudo",),
                kwargs={
                    "is_flag": True,
                    "help": "Allow setup docker to execute suggested sudo commands after confirmation.",
                },
            ),
            SetupOptionElement(
                param_decls=("--interactive/--no-interactive", "-i/-I"),
                kwargs={
                    "default": None,
                    "help": "Auto prompt on missing args, -i forces interactive, -I disables it.",
                },
            ),
        ),
    ),
    SetupCommandElement(
        name="claude",
        help="Setup Claude Code CLI and config files.",
        callback=claude_setup,
        options=(
            LOG_LEVEL_OPTION,
            SetupOptionElement(
                param_decls=("--interactive/--no-interactive", "-i/-I"),
                kwargs={
                    "default": None,
                    "help": "Auto prompt on missing args, -i forces interactive, -I disables it.",
                },
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
                kwargs={
                    "default": None,
                    "help": "Optional ANTHROPIC_SMALL_FAST_MODEL value.",
                },
            ),
            SetupOptionElement(
                param_decls=("--install-only",),
                kwargs={
                    "is_flag": True,
                    "help": "Only install or upgrade the CLI without writing config files.",
                },
            ),
        ),
    ),
    SetupCommandElement(
        name="chrome",
        help="Setup Chrome and Chromedriver.",
        callback=chrome_setup,
        options=(
            SetupOptionElement(
                param_decls=("--update",),
                kwargs={
                    "is_flag": True,
                    "help": "Update existing Chromedriver installation instead of exiting when already installed.",
                },
            ),
            SetupOptionElement(
                param_decls=("--interactive/--no-interactive", "-i/-I"),
                kwargs={
                    "default": None,
                    "help": "Auto prompt on missing args, -i forces interactive, -I disables it.",
                },
            ),
        ),
    ),
    SetupCommandElement(
        name="docker",
        help="Check Docker environment and optionally run suggested sudo commands.",
        callback=docker_setup,
        options=(
            LOG_LEVEL_OPTION,
            SetupOptionElement(
                param_decls=("--sudo",),
                kwargs={
                    "is_flag": True,
                    "help": "Allow setup docker to execute suggested sudo commands after confirmation.",
                },
            ),
            SetupOptionElement(
                param_decls=("--interactive/--no-interactive", "-i/-I"),
                kwargs={
                    "default": None,
                    "help": "Auto prompt on missing args, -i forces interactive, -I disables it.",
                },
            ),
        ),
    ),
    SetupCommandElement(
        name="frp",
        help="Setup FRP Client/Server.",
        callback=frp_setup,
        options=(
            LOG_LEVEL_OPTION,
            SetupOptionElement(
                param_decls=("--interactive/--no-interactive", "-i/-I"),
                kwargs={
                    "default": None,
                    "help": "Auto prompt on missing args, -i forces interactive, -I disables it.",
                },
            ),
        ),
    ),
    SetupCommandElement(
        name="nodejs",
        help="Setup nvm and Node.js (default LTS).",
        callback=nodejs_setup,
        options=(
            LOG_LEVEL_OPTION,
            SetupOptionElement(
                param_decls=("--interactive/--no-interactive", "-i/-I"),
                kwargs={
                    "default": None,
                    "help": "Auto prompt on missing args, -i forces interactive, -I disables it.",
                },
            ),
        ),
    ),
    SetupCommandElement(
        name="codex",
        help="Setup Codex CLI and config files.",
        callback=codex_setup,
        options=(
            LOG_LEVEL_OPTION,
            SetupOptionElement(
                param_decls=("--interactive/--no-interactive", "-i/-I"),
                kwargs={
                    "default": None,
                    "help": "Auto prompt on missing args, -i forces interactive, -I disables it.",
                },
            ),
            SetupOptionElement(
                param_decls=("--api-key", "--key"),
                kwargs={
                    "default": None,
                    "help": "OpenAI API key to write into Codex auth.json.",
                },
            ),
            SetupOptionElement(
                param_decls=("--base-url", "--url"),
                kwargs={
                    "default": None,
                    "help": "Optional base_url for model provider.",
                },
            ),
            SetupOptionElement(
                param_decls=("--model",),
                kwargs={"default": None, "help": "Optional default model name."},
            ),
            SetupOptionElement(
                param_decls=("-e", "--env"),
                kwargs={
                    "default": None,
                    "help": "Load OpenAI config from a .env file path or saved OpenAI profile name.",
                },
            ),
            SetupOptionElement(
                param_decls=("--install-only",),
                kwargs={
                    "is_flag": True,
                    "help": "Only install or upgrade the CLI without writing config files.",
                },
            ),
        ),
    ),
    SetupCommandElement(
        name="opencode",
        help="Setup OpenCode CLI and config files.",
        callback=opencode_setup,
        options=(
            LOG_LEVEL_OPTION,
            SetupOptionElement(
                param_decls=("--interactive/--no-interactive", "-i/-I"),
                kwargs={
                    "default": None,
                    "help": "Auto prompt on missing args, -i forces interactive, -I disables it.",
                },
            ),
            SetupOptionElement(
                param_decls=("--base-url", "--url"),
                kwargs={"default": None, "help": "Required base URL for the provider."},
            ),
            SetupOptionElement(
                param_decls=("--api-key", "--key"),
                kwargs={"default": None, "help": "Required API key for the provider."},
            ),
            SetupOptionElement(
                param_decls=("--model",),
                kwargs={"default": None, "help": "Required default model name."},
            ),
            SetupOptionElement(
                param_decls=("-e", "--env"),
                kwargs={
                    "default": None,
                    "help": "Load OpenAI config from a .env file path or saved OpenAI profile name.",
                },
            ),
            SetupOptionElement(
                param_decls=("--plugin",),
                kwargs={
                    "default": None,
                    "type": click.Choice(["auto-loop"]),
                    "help": "Optionally enable an OpenCode plugin preset such as opencode-auto-loop.",
                },
            ),
            SetupOptionElement(
                param_decls=("--install-only",),
                kwargs={
                    "is_flag": True,
                    "help": "Only install or upgrade the CLI without writing config files.",
                },
            ),
        ),
    ),
    SetupCommandElement(
        name="lark-cli",
        help="Setup official lark-cli and reuse ChatTool Feishu config.",
        callback=lark_cli_setup,
        options=(
            LOG_LEVEL_OPTION,
            SetupOptionElement(
                param_decls=("--interactive/--no-interactive", "-i/-I"),
                kwargs={
                    "default": None,
                    "help": "Auto prompt on missing args, -i forces interactive, -I disables it.",
                },
            ),
            SetupOptionElement(
                param_decls=("--app-id",),
                kwargs={"default": None, "help": "Lark/Feishu app id."},
            ),
            SetupOptionElement(
                param_decls=("--app-secret",),
                kwargs={"default": None, "help": "Lark/Feishu app secret."},
            ),
            SetupOptionElement(
                param_decls=("--brand",),
                kwargs={
                    "default": None,
                    "type": click.Choice(["feishu", "lark"]),
                    "help": "Official brand value written to lark-cli config.",
                },
            ),
            SetupOptionElement(
                param_decls=("-e", "--env"),
                kwargs={
                    "default": None,
                    "help": "Load Feishu config from a .env file path or saved Feishu profile name.",
                },
            ),
        ),
    ),
    SetupCommandElement(
        name="workspace",
        help="Initialize a human-AI collaboration workspace scaffold.",
        callback=workspace_setup,
        options=(
            SetupOptionElement(
                param_decls=("profile",),
                kwargs={"required": False},
            ),
            SetupOptionElement(
                param_decls=("workspace_dir",),
                kwargs={"required": False},
            ),
            SetupOptionElement(
                param_decls=("--language",),
                kwargs={
                    "default": "zh",
                    "type": click.Choice(["zh", "en"]),
                    "show_default": True,
                    "help": "Template language for generated workspace files.",
                },
            ),
            SetupOptionElement(
                param_decls=("--interactive/--no-interactive", "-i/-I"),
                kwargs={
                    "default": None,
                    "help": "Auto prompt on missing args, -i forces interactive, -I disables it.",
                },
            ),
            SetupOptionElement(
                param_decls=("--force", "-f"),
                kwargs={
                    "is_flag": True,
                    "help": "Overwrite existing generated files.",
                },
            ),
            SetupOptionElement(
                param_decls=("--dry-run",),
                kwargs={
                    "is_flag": True,
                    "help": "Print planned workspace files and directories without writing anything.",
                },
            ),
            SetupOptionElement(
                param_decls=("--with-chattool/--no-chattool",),
                kwargs={
                    "default": False,
                    "help": "Optionally clone/update ChatTool in the workspace root and sync its skills into docs/skills/.",
                },
            ),
            SetupOptionElement(
                param_decls=("--chattool-source", "--source"),
                kwargs={
                    "default": None,
                    "help": "Git URL or local ChatTool repo path used when --with-chattool is enabled.",
                },
            ),
            SetupOptionElement(
                param_decls=("--with-opencode-loop/--no-opencode-loop",),
                kwargs={
                    "default": False,
                    "help": "Use the OpenCode loop-aware workspace template and install local chatloop assets.",
                },
            ),
        ),
    ),
)
