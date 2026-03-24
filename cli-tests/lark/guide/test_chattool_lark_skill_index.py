from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_INDEX = REPO_ROOT / "skills" / "feishu" / "SKILL.md"
SKILL_ROOT = REPO_ROOT / "skills" / "feishu"


def _extract_mapping_section(text: str) -> str:
    match = re.search(
        r"## Skill 与 CLI Tests 对应\s*\n(.*?)(?:\n## |\Z)",
        text,
        re.S,
    )
    assert match, "Skill mapping section not found in skills/feishu/SKILL.md"
    return match.group(1)


def _parse_skill_test_mapping(text: str) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    current_skill: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue

        paths = re.findall(r"`([^`]+)`", stripped)
        if not paths:
            continue

        if line.startswith("- "):
            current_skill = paths[0]
            mapping.setdefault(current_skill, [])
            continue

        if current_skill is None:
            continue

        mapping[current_skill].extend(paths)

    return mapping


def test_chattool_lark_skill_index():
    text = SKILL_INDEX.read_text(encoding="utf-8")
    mapping = _parse_skill_test_mapping(_extract_mapping_section(text))

    skill_docs = sorted(
        path.relative_to(SKILL_ROOT).as_posix()
        for path in SKILL_ROOT.rglob("*.md")
    )
    mapped_docs = sorted(mapping)

    assert mapped_docs == skill_docs, (
        "Feishu skill docs and mapped test docs are out of sync.\n"
        f"mapped={mapped_docs}\n"
        f"actual={skill_docs}"
    )

    for skill_doc, test_docs in mapping.items():
        assert test_docs, f"{skill_doc} has no mapped cli-tests markdown"
        for test_doc in test_docs:
            test_path = REPO_ROOT / test_doc
            assert test_path.exists(), f"Mapped test doc does not exist: {test_doc}"

