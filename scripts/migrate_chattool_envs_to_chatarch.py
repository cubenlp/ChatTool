#!/usr/bin/env python3
"""Manually copy legacy ChatTool env profiles into the ChatArch env root."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


DEFAULT_LEGACY_ENVS = Path.home() / ".config" / "chattool" / "envs"


def default_chatarch_envs() -> Path:
    chatarch_home = Path(os.environ.get("CHATARCH_HOME", Path.home() / ".chatarch"))
    return chatarch_home / "envs"


def copy_tree(src: Path, dst: Path, *, overwrite: bool, dry_run: bool) -> tuple[int, int]:
    copied = 0
    skipped = 0
    for item in sorted(src.rglob("*")):
        rel = item.relative_to(src)
        target = dst / rel
        if item.is_dir():
            if not dry_run:
                target.mkdir(parents=True, exist_ok=True)
            continue
        if target.exists() and not overwrite:
            print(f"skip existing: {target}")
            skipped += 1
            continue
        action = "overwrite" if target.exists() else "copy"
        print(f"{action}: {item} -> {target}")
        copied += 1
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
    return copied, skipped


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Copy old ChatTool env profiles from ~/.config/chattool/envs to "
            "$CHATARCH_HOME/envs. Runtime code does not read the old path."
        )
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_LEGACY_ENVS,
        help=f"legacy env root, default: {DEFAULT_LEGACY_ENVS}",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=default_chatarch_envs(),
        help="new env root, default: $CHATARCH_HOME/envs or ~/.chatarch/envs",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="overwrite existing files in the target env root",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print planned copies without writing files",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.expanduser()
    target = args.target.expanduser()

    if not source.exists():
        print(f"legacy env root does not exist: {source}")
        return 1
    if not source.is_dir():
        print(f"legacy env root is not a directory: {source}")
        return 1

    print(f"source: {source}")
    print(f"target: {target}")
    print(f"mode: {'dry-run, ' if args.dry_run else ''}{'overwrite' if args.overwrite else 'skip existing'}")

    copied, skipped = copy_tree(
        source,
        target,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
    )
    print(f"done: {copied} file(s) copied, {skipped} existing file(s) skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
