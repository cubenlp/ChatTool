from __future__ import annotations

from pathlib import Path

import click


def download_binary(url: str, output: str | Path, headers: dict | None = None) -> bool:
    import requests

    resp = requests.get(url, headers=headers or {})
    if resp.status_code != 200:
        click.echo(f"Failed to download image: {resp.status_code}")
        return False
    output_path = Path(output)
    output_path.write_bytes(resp.content)
    click.echo(f"Image saved to {output_path}")
    return True


def echo_model_list(models, title: str) -> None:
    click.echo(title)
    for item in models:
        if isinstance(item, dict):
            model_id = item.get("id") or item.get("name") or str(item)
        else:
            model_id = str(item)
        click.echo(f"- {model_id}")
