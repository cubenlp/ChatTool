import importlib

import click
from chattool.client.main import LazyGroup


def _load_attr(module_path: str, attr: str):
    module = importlib.import_module(module_path)
    return getattr(module, attr)


def _load_capture():
    command = _load_attr("chattool.serve.capture", "main")
    command.short_help = "Run the screenshot capture server."
    return command


def _load_cert():
    command = _load_attr("chattool.serve.cert_server", "cert_app")
    command.short_help = "Run the certificate service."
    return command


def _load_lark():
    command = _load_attr("chattool.serve.lark_serve", "cli")
    command.short_help = "Run the Lark webhook service."
    return command


def _load_svg2gif():
    command = _load_attr("chattool.serve.svg2gif", "svg2gif_app")
    command.short_help = "Run the SVG-to-GIF conversion service."
    return command


@click.group(name="serve", cls=LazyGroup)
def serve_cli():
    """Local server tools."""
    pass


serve_cli._lazy_commands.update(
    {
        "capture": _load_capture,
        "cert": _load_cert,
        "lark": _load_lark,
        "svg2gif": _load_svg2gif,
    }
)
serve_cli._lazy_command_help.update(
    {
        "capture": "Run the screenshot capture server.",
        "cert": "Run the certificate service.",
        "lark": "Run the Lark webhook service.",
        "svg2gif": "Run the SVG-to-GIF conversion service.",
    }
)
