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
    return LazyGroup(
        name="serve",
        help="Local server tools.",
        lazy_commands={
            "capture": lambda: _load_attr("chattool.serve.capture", "main"),
            "cert": lambda: _load_attr("chattool.serve.cert_server", "cert_app"),
            "lark": lambda: _load_attr("chattool.serve.lark_serve", "cli"),
        },
    )


def _build_client_group() -> click.Command:
    return LazyGroup(
        name="client",
        help="Remote client tools.",
        lazy_commands={
            "cert": lambda: _load_attr("chattool.cli.client.cert_client", "cert_client"),
        },
    )


@click.group(cls=LazyGroup)
def cli():
    """ChatTool CLI - Unified entry point for ChatTool services and scripts."""
    pass


cli._lazy_commands.update({
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
    "skill": lambda: _load_attr("chattool.skill.cli", "skill_cli"),
    "setup": lambda: _load_attr("chattool.setup.cli", "setup_group"),
    "docker": lambda: _load_attr("chattool.docker.cli", "docker_cmd"),
})


def main():
    cli()


if __name__ == "__main__":
    main()
