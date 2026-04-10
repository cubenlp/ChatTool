from pathlib import Path


def test_all_skills_have_chinese_variant():
    skills_dir = Path(__file__).resolve().parents[3] / "skills"
    missing = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        if not (skill_dir / "SKILL.md").exists():
            continue
        if skill_dir.name == "feishu":
            continue
        if not (skill_dir / "SKILL.zh.md").exists():
            missing.append(skill_dir.name)

    assert not missing, f"Missing SKILL.zh.md for: {', '.join(missing)}"
