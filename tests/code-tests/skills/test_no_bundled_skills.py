from pathlib import Path

from chattool.skill.platforms import find_repo_skills_dir, resolve_source_dir


def test_chattool_no_longer_ships_repo_bundled_skills(monkeypatch):
    repo_root = Path(__file__).resolve().parents[3]

    assert not (repo_root / "skills").exists()
    assert find_repo_skills_dir() is None

    monkeypatch.delenv("CHATTOOL_SKILLS_DIR", raising=False)
    monkeypatch.setattr(
        "chattool.config.SkillsConfig.CHATTOOL_SKILLS_DIR",
        type("Field", (), {"value": ""})(),
    )

    assert resolve_source_dir(None) is None
