from pathlib import Path

import pytest
from click.testing import CliRunner

from chattool.client.main import cli


@pytest.fixture
def runner():
    return CliRunner()


def _write_skill(skill_dir: Path, content: str) -> None:
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")


def test_skill_install_copies_valid_skill(runner, tmp_path):
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    _write_skill(
        source / "demo",
        """---
name: demo
description: Demo skill for install testing.
---

# Demo
""",
    )

    result = runner.invoke(
        cli,
        ["skill", "install", "demo", "--source", str(source), "--dest", str(dest)],
    )

    assert result.exit_code == 0
    assert "Installed skills to" in result.output
    assert (dest / "demo" / "SKILL.md").exists()


def test_skill_install_rejects_missing_frontmatter(runner, tmp_path):
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    _write_skill(
        source / "legacy",
        """# Legacy Skill

No frontmatter here.
""",
    )

    result = runner.invoke(
        cli,
        ["skill", "install", "legacy", "--source", str(source), "--dest", str(dest)],
    )

    assert result.exit_code != 0
    assert "Invalid skill definitions detected" in result.output
    assert "missing YAML frontmatter delimited by ---" in result.output
    assert not (dest / "legacy").exists()


def test_skill_install_rejects_missing_required_frontmatter_keys(runner, tmp_path):
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    _write_skill(
        source / "incomplete",
        """---
name: incomplete
---

# Incomplete
""",
    )

    result = runner.invoke(
        cli,
        ["skill", "install", "incomplete", "--source", str(source), "--dest", str(dest)],
    )

    assert result.exit_code != 0
    assert "missing required frontmatter keys: description" in result.output
    assert not (dest / "incomplete").exists()


def test_skill_install_all_aborts_when_any_target_is_invalid(runner, tmp_path):
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    _write_skill(
        source / "good",
        """---
name: good
description: Good skill.
---

# Good
""",
    )
    _write_skill(
        source / "bad",
        """# Bad
""",
    )

    result = runner.invoke(
        cli,
        ["skill", "install", "--all", "--source", str(source), "--dest", str(dest)],
    )

    assert result.exit_code != 0
    assert "missing YAML frontmatter delimited by ---" in result.output
    assert not (dest / "good").exists()
    assert not (dest / "bad").exists()
