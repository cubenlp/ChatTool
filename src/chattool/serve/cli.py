import click

from .capture import main as capture_main
from .cert_server import cert_app
from .lark_serve import cli as lark_serve_cli
from .svg2gif import svg2gif_app


@click.group(name="serve")
def serve_cli():
    """Local server tools."""
    pass


serve_cli.add_command(capture_main, name="capture")
serve_cli.add_command(cert_app, name="cert")
serve_cli.add_command(lark_serve_cli, name="lark")
serve_cli.add_command(svg2gif_app, name="svg2gif")
