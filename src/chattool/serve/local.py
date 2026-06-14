from __future__ import annotations

import http.server
import socketserver
import webbrowser
from functools import partial
from pathlib import Path
from urllib.parse import quote

import click


def resolve_local_target(target: str | None, html_name: str | None) -> dict[str, str]:
    """Resolve a directory or HTML file into a static root and URL path."""

    raw_target = Path(target or ".").expanduser()
    target_path = raw_target.resolve()

    if target_path.is_file():
        if html_name:
            raise click.UsageError("--html can only be used when TARGET is a directory.")
        root = target_path.parent
        html_path = target_path
    elif target_path.is_dir():
        root = target_path
        html_path = (root / (html_name or "index.html")).resolve()
        try:
            html_path.relative_to(root)
        except ValueError as exc:
            raise click.UsageError("--html must resolve inside TARGET directory.") from exc
    else:
        raise click.UsageError(f"TARGET does not exist: {raw_target}")

    if not html_path.exists():
        raise click.UsageError(f"HTML file does not exist: {html_path}")
    if not html_path.is_file():
        raise click.UsageError(f"HTML path is not a file: {html_path}")

    return {
        "root": str(root),
        "html": str(html_path),
        "path": "/" + quote(str(html_path.relative_to(root)).replace("\\", "/")),
    }


@click.command(name="local")
@click.argument("target", required=False)
@click.option("--html", "html_name", default=None, help="HTML file inside TARGET directory. Defaults to index.html.")
@click.option("--host", default="127.0.0.1", show_default=True, help="Bind host.")
@click.option("--port", default=8765, show_default=True, type=int, help="Bind port.")
@click.option("--open/--no-open", "open_browser", default=True, show_default=True, help="Open the URL in a browser.")
@click.option("--dry-run", is_flag=True, help="Print resolved server info without starting the server.")
def local(target: str | None, html_name: str | None, host: str, port: int, open_browser: bool, dry_run: bool) -> None:
    """Serve a local directory or HTML file over HTTP."""

    resolved = resolve_local_target(target, html_name)
    url = f"http://{host}:{port}{resolved['path']}"
    click.echo(f"Root: {resolved['root']}")
    click.echo(f"HTML: {resolved['html']}")
    click.echo(f"URL:  {url}")
    if dry_run:
        return

    handler = partial(http.server.SimpleHTTPRequestHandler, directory=resolved["root"])
    with socketserver.TCPServer((host, port), handler) as httpd:
        click.echo("Press Ctrl+C to stop.")
        if open_browser:
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            click.echo("\nStopped.")
