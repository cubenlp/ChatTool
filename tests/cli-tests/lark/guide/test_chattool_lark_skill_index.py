from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
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
    expected_en = [
        "lark-cli",
        "docs/blog/agent-cli/lark-cli-guide.md",
        "docs/blog/lark-message-session-debug.md",
        "lark-cli/",
        "lark-cli im",
        "docs +create",
        "permission.members",
        "wiki spaces get_node",
        "chattool lark info",
        "chattool lark send",
        "chattool lark chat",
        "--no-wait",
        "--device-code",
    ]
    expected_zh = [
        "docs/blog/agent-cli/lark-cli-guide.md",
        "docs/blog/lark-message-session-debug.md",
        "lark-cli/",
        "lark-cli im",
        "docs +create",
        "permission.members",
        "wiki spaces get_node",
        "chattool lark info",
        "chattool lark send",
        "chattool lark chat",
        "--no-wait",
        "--device-code",
    ]

    for snippet in expected_en:
        assert snippet in text
    for snippet in expected_zh:
        assert snippet in text_zh
