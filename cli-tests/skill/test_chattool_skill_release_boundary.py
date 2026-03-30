from pathlib import Path


def test_chattool_skill_release_boundary():
    repo_root = Path(__file__).resolve().parents[2]

    dev_en = (repo_root / "skills/chattool-dev-review/SKILL.md").read_text(encoding="utf-8")
    dev_zh = (repo_root / "skills/chattool-dev-review/SKILL.zh.md").read_text(encoding="utf-8")
    release_en = (repo_root / "skills/chattool-release/SKILL.md").read_text(encoding="utf-8")
    release_zh = (repo_root / "skills/chattool-release/SKILL.zh.md").read_text(encoding="utf-8")
    practice_en = (repo_root / "skills/practice-make-perfact/SKILL.md").read_text(encoding="utf-8")
    practice_zh = (repo_root / "skills/practice-make-perfact/SKILL.zh.md").read_text(encoding="utf-8")

    assert "$chattool-release" in dev_en
    assert "$chattool-release" in dev_zh
    assert "release.log" in dev_en
    assert "release.log" in dev_zh

    assert "Do not tag from an unmerged PR head." in release_en
    assert "Publish Package" in release_en
    assert "release.log" in release_en
    assert "不要从未合并的 PR 分支 head 打 tag。" in release_zh
    assert "Publish Package" in release_zh
    assert "release.log" in release_zh

    assert "$chattool-release" in practice_en
    assert "$chattool-release" in practice_zh
