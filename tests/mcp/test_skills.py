import pytest

skills_module = pytest.importorskip("chattool.mcp.skills")
get_skill = skills_module.get_skill
load_skills = skills_module.load_skills


def test_load_skills_returns_items():
    skills = load_skills(lang="zh")
    assert len(skills) >= 3
    names = {item.name for item in skills}
    assert "dns" in names
    assert "cert-manager" in names


def test_get_skill_by_name_and_dir():
    skill_by_name = get_skill("dns", lang="en")
    assert skill_by_name is not None
    assert skill_by_name.name == "dns"
    skill_by_dir = get_skill("network-scanner", lang="zh")
    assert skill_by_dir is not None
    assert skill_by_dir.skill_dir == "network-scanner"
