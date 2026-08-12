from __future__ import annotations

import importlib
from typing import Callable

import click

from chattool import __version__


class LazyGroup(click.Group):
    def __init__(
        self,
        *args,
        lazy_commands: dict[str, Callable[[], click.Command]] | None = None,
        lazy_command_help: dict[str, str] | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._lazy_commands = dict(lazy_commands or {})
        self._lazy_command_help = dict(lazy_command_help or {})

    def list_commands(self, ctx: click.Context) -> list[str]:
        commands = set(self.commands)
        commands.update(self._lazy_commands)
        return sorted(commands)

    def get_command(self, ctx: click.Context, name: str) -> click.Command | None:
        if name in self._lazy_commands:
            self.commands[name] = self._lazy_commands.pop(name)()
        return super().get_command(ctx, name)

    def format_commands(
        self, ctx: click.Context, formatter: click.HelpFormatter
    ) -> None:
        rows = []
        for subcommand in self.list_commands(ctx):
            if subcommand in self.commands:
                cmd = self.commands[subcommand]
                if cmd is None or cmd.hidden:
                    continue
                help_text = cmd.get_short_help_str()
            else:
                help_text = self._lazy_command_help.get(subcommand, "")
            rows.append((subcommand, help_text))

        if rows:
            with formatter.section("Commands"):
                formatter.write_dl(rows)


_TREE_PARAM_PURPOSES = {
    "help": "Show help for the current command.",
    "version": "Show package version.",
    "tree": "Print the registered CLI tree.",
}


def _load_attr(module_path: str, attr: str) -> click.Command:
    module = importlib.import_module(module_path)
    return getattr(module, attr)


def _build_serve_group() -> click.Command:
    return _load_attr("chattool.serve.cli", "serve_cli")


def _build_client_group() -> click.Command:
    return LazyGroup(
        name="client",
        help="Remote client tools.",
        lazy_commands={
            "cert": lambda: _load_attr("chattool.client.cert_client", "cert_client"),
            "svg2gif": lambda: _load_attr(
                "chattool.client.svg2gif_client", "svg2gif_client"
            ),
        },
        lazy_command_help={
            "cert": "Manage certificates through the remote cert service.",
            "svg2gif": "Convert SVG to GIF through the remote svg2gif service.",
        },
    )


def _command_help(command: click.Command) -> str:
    if command.help:
        return command.help
    if command.short_help:
        return command.short_help
    if command.callback and command.callback.__doc__:
        return command.callback.__doc__.strip()
    return ""


def _param_signature(param: click.Parameter) -> str:
    opts = getattr(param, "opts", None) or []
    secondary = getattr(param, "secondary_opts", None) or []
    names = [*opts, *secondary]
    if names:
        return "/".join(names)
    return param.human_readable_name.upper().replace("_", "-")


def _param_purpose(param: click.Parameter) -> str:
    if param.name in _TREE_PARAM_PURPOSES:
        return _TREE_PARAM_PURPOSES[param.name]
    if isinstance(param, click.Option) and param.help:
        return param.help.rstrip(".") + "."
    return "Option registered by Click."


def _iter_command_rows(command: click.Command) -> list[tuple[str, str]]:
    rows = [("--help", _TREE_PARAM_PURPOSES["help"])]
    for param in command.params:
        if getattr(param, "hidden", False):
            continue
        rows.append((_param_signature(param), _param_purpose(param)))
    if isinstance(command, LazyGroup):
        ctx = click.Context(command)
        for name in command.list_commands(ctx):
            if name in command.commands:
                child = command.commands[name]
                if child is None or child.hidden:
                    continue
            help_text = command._lazy_command_help.get(name)
            if help_text is None and name in command.commands:
                help_text = command.commands[name].get_short_help_str()
            rows.append((name, help_text or ""))
    elif isinstance(command, click.Group):
        for name, child in sorted(command.commands.items()):
            if child is None or child.hidden:
                continue
            rows.append((name, child.get_short_help_str()))
    return rows


def render_command_tree(command: click.Command, name: str = "chattool") -> str:
    lines = [f"{name}  # {_command_help(command)}"]
    rows = _iter_command_rows(command)
    for index, (label, purpose) in enumerate(rows):
        connector = "└──" if index == len(rows) - 1 else "├──"
        lines.append(f"{connector} {label}  # {purpose}")
    return "\n".join(lines)


@click.group(cls=LazyGroup, invoke_without_command=True)
@click.version_option(__version__, prog_name="chattool")
@click.option(
    "--tree",
    "show_tree",
    is_flag=True,
    help="Print the registered CLI tree.",
)
@click.pass_context
def cli(ctx: click.Context, show_tree: bool) -> None:
    """Unified entry point for ChatTool services and scripts."""
    if show_tree:
        click.echo(render_command_tree(ctx.command, "chattool"))
        ctx.exit(0)
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit(0)


cli._lazy_commands.update(
    {
        "serve": _build_serve_group,
        "client": _build_client_group,
        "nginx": lambda: _load_attr("chattool.tools.nginx.cli", "cli"),
        "mcp": lambda: _load_attr("chattool.mcp.cli", "cli"),
        "tplogin": lambda: _load_attr("chattool.tools.tplogin_cli", "cli"),
        "browser": lambda: _load_attr("chattool.tools.browser.cli", "cli"),
        "skill": lambda: _load_attr("chattool.skill.cli", "skill_cli"),
        "cc": lambda: _load_attr("chattool.tools.cc.cli", "cli"),
        "docker": lambda: _load_attr("chattool.docker.cli", "docker_cmd"),
        "explore": lambda: _load_attr("chattool.explore.cli", "explore_cli"),
        "crs": lambda: _load_attr("chattool.tools.crs.cli", "cli"),
    }
)
cli._lazy_command_help.update(
    {
        "browser": "Browser automation helpers.",
        "cc": "cc-connect helper commands.",
        "client": "Remote client tools.",
        "crs": "Claude Relay Service helper commands.",
        "docker": "Docker utility commands.",
        "explore": "Research and data exploration helpers.",
        "mcp": "MCP server inspection and launch helpers.",
        "nginx": "Nginx configuration generation helpers.",
        "serve": "Local service helpers.",
        "skill": "Install and manage ChatTool skills.",
        "tplogin": "TP-Link router helpers.",
    }
)


def main():
    cli()


if __name__ == "__main__":
    main()
