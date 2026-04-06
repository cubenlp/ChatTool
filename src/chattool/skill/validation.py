from __future__ import annotations

import re
from pathlib import Path

REQUIRED_FRONTMATTER_KEYS = ("name", "description")


def list_skill_dirs(source_dir: Path) -> list[str]:
    if not source_dir.exists():
        return []
    skills = []
    for entry in source_dir.iterdir():
        if entry.is_dir() and (entry / "SKILL.md").exists():
            skills.append(entry.name)
    return sorted(skills)


def extract_frontmatter_values(skill_md: Path) -> tuple[dict[str, str], list[str]]:
    try:
        content = skill_md.read_text(encoding="utf-8")
    except OSError as exc:
        return {}, [f"failed to read file: {exc}"]

    lines = content.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, ["missing YAML frontmatter delimited by ---"]

    closing_index = None
    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing_index = idx
            break

    if closing_index is None:
        return {}, ["missing closing YAML frontmatter delimiter ---"]

    values = {}
    key_pattern = re.compile(r"^([A-Za-z0-9_-]+)\s*:")
    for raw_line in lines[1:closing_index]:
        if not raw_line.strip() or raw_line[:1].isspace():
            continue
        match = key_pattern.match(raw_line)
        if match:
            key = match.group(1)
            value = raw_line.split(":", 1)[1].strip().strip('"').strip("'")
            values[key] = value

    return values, []


def validate_skill_dir(skill_dir: Path) -> list[str]:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return ["missing SKILL.md"]

    values, errors = extract_frontmatter_values(skill_md)
    if errors:
        return errors

    missing = [key for key in REQUIRED_FRONTMATTER_KEYS if key not in values]
    if missing:
        return [f"missing required frontmatter keys: {', '.join(missing)}"]

    return []
