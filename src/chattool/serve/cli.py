import importlib

import click
from chattool.client.main import LazyGroup


def _load_attr(module_path: str, attr: str):
    module = importlib.import_module(module_path)
    return getattr(module, attr)


@click.group(name="serve", cls=LazyGroup)
def serve_cli():
    """Local server tools."""
    pass


serve_cli._lazy_commands.update({
    "capture": lambda: _load_attr("chattool.serve.capture", "main"),
    "cert": lambda: _load_attr("chattool.serve.cert_server", "cert_app"),
    "lark": lambda: _load_attr("chattool.serve.lark_serve", "cli"),
    "svg2gif": lambda: _load_attr("chattool.serve.svg2gif", "svg2gif_app"),
})
