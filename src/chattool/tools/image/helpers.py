from __future__ import annotations

from datetime import datetime
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


def slugify(text: str, max_len: int = 40) -> str:
    out = []
    prev_dash = False
    for ch in text.lower():
        if ch.isalnum():
            out.append(ch)
            prev_dash = False
        elif not prev_dash:
            out.append("-")
            prev_dash = True
    slug = "".join(out).strip("-")
    return slug[:max_len].rstrip("-") or "image"


def resolve_generated_output_path(
    output: str | Path | None = None,
    *,
    provider: str | None = None,
    model: str | None = None,
    prompt: str | None = None,
    suffix: str = ".png",
    base_dir: str | Path | None = None,
) -> Path:
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path

    root = Path(base_dir) if base_dir else Path.cwd() / "generated"
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    parts = ["image"]
    if provider:
        parts.append(slugify(provider))
    if model:
        parts.append(slugify(model))
    elif prompt:
        parts.append(slugify(prompt))
    filename = "_".join(filter(None, parts + [stamp])) + suffix
    return root / filename


def resolve_prompt_slug_output_path(
    prompt: str,
    output: str | Path | None = None,
    *,
    suffix: str = ".png",
    base_dir: str | Path | None = None,
) -> Path:
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path

    root = Path(base_dir) if base_dir else Path.cwd() / "generated"
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return root / f"{stamp}_{slugify(prompt)}{suffix}"


def save_binary(content: bytes, output: str | Path) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(content)
    return output_path
