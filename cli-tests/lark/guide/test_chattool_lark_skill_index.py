from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_INDEX = REPO_ROOT / "skills" / "feishu" / "SKILL.md"
SKILL_INDEX_ZH = REPO_ROOT / "skills" / "feishu" / "SKILL.zh.md"
SKILL_ROOT = REPO_ROOT / "skills" / "feishu"


def test_chattool_lark_skill_index():
    text = SKILL_INDEX.read_text(encoding="utf-8")
    text_zh = SKILL_INDEX_ZH.read_text(encoding="utf-8")
    skill_docs = sorted(
        path.relative_to(SKILL_ROOT).as_posix() for path in SKILL_ROOT.rglob("*.md")
    )

    assert skill_docs == ["SKILL.md", "SKILL.zh.md"], (
        f"Unexpected files left under skills/feishu: {skill_docs}"
    )
    assert "lark-cli" in text
    assert "docs/blog/agent-cli/lark-cli-guide.md" in text
    assert "docs/blog/lark-message-session-debug.md" in text
    assert "lark-cli/" in text
    assert "docs +create" in text
    assert "permission.members" in text
    assert "wiki spaces get_node" in text
    assert "chattool lark info" in text
    assert "lark-cli im" in text
    assert "docs/blog/lark-message-session-debug.md" in text_zh
    assert "chattool lark send" in text_zh
