from pathlib import Path


def test_chattool_skill_practice_make_perfact_reference():
    repo_root = Path(__file__).resolve().parents[3]

    skill_en = (repo_root / "skills/practice-make-perfact/SKILL.md").read_text(
        encoding="utf-8"
    )
    skill_zh = (repo_root / "skills/practice-make-perfact/SKILL.zh.md").read_text(
        encoding="utf-8"
    )
    reference = (
        repo_root / "skills/practice-make-perfact/references/cli-reference.md"
    ).read_text(encoding="utf-8")

    assert "cli-reference.md" in skill_en
    assert "cli-reference.md" in skill_zh
    assert "chattool lark" in reference
    assert "chattool gh" in reference
    assert "chattool setup" in reference
