from __future__ import annotations

import os
import shutil
from pathlib import Path

import click


def resolve_opencode_home() -> Path:
    env_home = os.getenv("OPENCODE_HOME")
    if env_home:
        return Path(env_home).expanduser().resolve()
    return (Path.home() / ".config" / "opencode").resolve()


def build_chatloop_plugin_entry(opencode_home: Path) -> str:
    plugin_file = (opencode_home / "plugins" / "chatloop" / "index.ts").resolve()
    return f"file://{plugin_file}"


def _copy_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if dst.is_file() or dst.is_symlink():
            dst.unlink()
        else:
            shutil.rmtree(dst)
    shutil.copytree(src, dst)


def install_chatloop_assets(opencode_home: Path | None = None) -> dict[str, Path | str]:
    target_home = (opencode_home or resolve_opencode_home()).expanduser().resolve()
    assets_root = Path(__file__).resolve().parent / "assets" / "opencode_chatloop"
    if not assets_root.exists():
        raise click.ClickException(f"Missing opencode chatloop assets: {assets_root}")

    plugin_dst = target_home / "plugins" / "chatloop"
    commands_dst = target_home / "command"
    _copy_tree(assets_root / "plugins" / "chatloop", plugin_dst)
    commands_dst.mkdir(parents=True, exist_ok=True)
    for command_file in (assets_root / "commands").glob("*.md"):
        shutil.copy2(command_file, commands_dst / command_file.name)

    return {
        "opencode_home": target_home,
        "plugin_dir": plugin_dst,
        "commands_dir": commands_dst,
        "plugin_entry": build_chatloop_plugin_entry(target_home),
    }
