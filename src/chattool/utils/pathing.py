from __future__ import annotations

from pathlib import Path

from chattool.utils.custom_logger import setup_logger

logger = setup_logger("pathing")


def normalize_path(value) -> Path | None:
    if value is None:
        return None
    if isinstance(value, Path):
        return value.expanduser().resolve()
    text = str(value).strip()
    if not text:
        return None
    return Path(text).expanduser().resolve()


def resolve_workspace_dir(workspace_dir=None) -> Path:
    return normalize_path(workspace_dir) or Path.cwd().resolve()


def display_path(path: Path, workspace_dir: Path) -> str:
    try:
        return str(path.relative_to(workspace_dir))
    except ValueError:
        return str(path)


def write_text_file(path: Path, content: str, force: bool) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        logger.info(f"Skip existing file: {path}")
        return "skipped"
    action = "updated" if path.exists() else "created"
    path.write_text(content, encoding="utf-8")
    logger.info(f"{action.capitalize()} file: {path}")
    return action
