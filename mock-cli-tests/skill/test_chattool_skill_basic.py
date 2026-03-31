from pathlib import Path

import pytest

from click.testing import CliRunner

from chattool.skill.cli import skill_cli


pytestmark = pytest.mark.mock_cli


def _write_skill(source_dir: Path, name: str) -> None:
    skill_dir = source_dir / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "\n".join(
            [
                "---",
                f"name: {name}",
                f"description: skill {name}",
                "---",
                "",
                f"# {name}",
            ]
        ),
        encoding="utf-8",
    )


def test_skill_install_prompts_when_name_missing(tmp_path, monkeypatch):
    source_dir = tmp_path / "skills"
    _write_skill(source_dir, "alpha")
    _write_skill(source_dir, "beta")

    codex_home = tmp_path / "codex-home"
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    monkeypatch.setattr("chattool.skill.cli.is_interactive_available", lambda: True)
    monkeypatch.setattr("chattool.skill.cli.ask_select", lambda message, choices: "alpha")

    result = CliRunner().invoke(
        skill_cli,
        ["install", "--source", str(source_dir)],
    )

    assert result.exit_code == 0
    assert "Missing skill name" not in result.output
    assert (codex_home / "skills" / "alpha").exists()
