import importlib
from typing import Callable

import click


class LazyGroup(click.Group):
    def __init__(self, *args, lazy_commands: dict[str, Callable[[], click.Command]] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._lazy_commands = dict(lazy_commands or {})

    def list_commands(self, ctx: click.Context) -> list[str]:
        commands = set(self.commands)
        commands.update(self._lazy_commands)
        return sorted(commands)

    def get_command(self, ctx: click.Context, name: str) -> click.Command | None:
        if name in self._lazy_commands:
            self.commands[name] = self._lazy_commands.pop(name)()
        return super().get_command(ctx, name)


def _load_attr(module_path: str, attr: str) -> click.Command:
    module = importlib.import_module(module_path)
    return getattr(module, attr)


def _load_dns_group() -> click.Command:
    dns_group = _load_attr("chattool.tools.dns.cli", "cli")
    ssl_cmd = _load_attr("chattool.tools.cert.cli", "main")
    dns_group.add_command(ssl_cmd, name="cert-update")
    return dns_group


def _build_serve_group() -> click.Command:
    return _load_attr("chattool.serve.cli", "serve_cli")


def _build_client_group() -> click.Command:
    return LazyGroup(
        name="client",
        help="Remote client tools.",
        lazy_commands={
            "cert": lambda: _load_attr("chattool.client.cert_client", "cert_client"),
            "svg2gif": lambda: _load_attr("chattool.client.svg2gif_client", "svg2gif_client"),
        },
    )


@click.group(cls=LazyGroup)
def cli():
    """ChatTool CLI - Unified entry point for ChatTool services and scripts."""
    pass


cli._lazy_commands.update({
    "env": lambda: _load_attr("chattool.config.cli", "cli"),
    "dns": _load_dns_group,
    "serve": _build_serve_group,
    "client": _build_client_group,
    "network": lambda: _load_attr("chattool.tools.network.cli", "network"),
    "mcp": lambda: _load_attr("chattool.mcp.cli", "cli"),
    "lark": lambda: _load_attr("chattool.tools.lark.cli", "cli"),
    "image": lambda: _load_attr("chattool.tools.image.cli", "cli"),
    "tplogin": lambda: _load_attr("chattool.tools.tplogin_cli", "cli"),
    "gh": lambda: _load_attr("chattool.tools.github.cli", "cli"),
    "browser": lambda: _load_attr("chattool.tools.browser.cli", "cli"),
    "zulip": lambda: _load_attr("chattool.tools.zulip.cli", "cli"),
    "skill": lambda: _load_attr("chattool.skills.cli", "skill_cli"),
    "setup": lambda: _load_attr("chattool.setup.cli", "setup_group"),
    "cc": lambda: _load_attr("chattool.tools.cc.cli", "cli"),
    "docker": lambda: _load_attr("chattool.docker.cli", "docker_cmd"),
    "explore": lambda: _load_attr("chattool.explore.cli", "explore_cli"),
})


def main():
    cli()


if __name__ == "__main__":
    main()
