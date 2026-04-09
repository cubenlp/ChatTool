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
    monkeypatch.setenv("CHATTOOL_SKILL_PLATFORM", "codex")
    monkeypatch.setattr("chattool.skill.cli.is_interactive_available", lambda: True)
    monkeypatch.setattr(
        "chattool.skill.interaction.ask_checkbox_with_controls",
        lambda *args, **kwargs: ["alpha"],
    )

    result = CliRunner().invoke(
        skill_cli,
        ["install", "--source", str(source_dir)],
    )

    assert result.exit_code == 0
    assert "Missing skill name" not in result.output
    assert (codex_home / "skills" / "alpha").exists()


def test_skill_install_prompts_for_platform_before_skill(tmp_path, monkeypatch):
    source_dir = tmp_path / "skills"
    _write_skill(source_dir, "alpha")

    opencode_home = tmp_path / "opencode-home"
    monkeypatch.setenv("OPENCODE_HOME", str(opencode_home))
    monkeypatch.delenv("CHATTOOL_SKILL_PLATFORM", raising=False)
    monkeypatch.setattr("chattool.skill.cli.is_interactive_available", lambda: True)

    selections = iter(["opencode"])
    monkeypatch.setattr(
        "chattool.skill.interaction.ask_select",
        lambda message, choices: next(selections),
    )
    monkeypatch.setattr(
        "chattool.skill.interaction.ask_checkbox_with_controls",
        lambda *args, **kwargs: ["alpha"],
    )

    result = CliRunner().invoke(
        skill_cli,
        ["install", "--source", str(source_dir)],
    )

    assert result.exit_code == 0
    assert (opencode_home / "skills" / "alpha" / "SKILL.md").exists()


def test_skill_install_opencode_uses_global_skills_dir(tmp_path, monkeypatch):
    source_dir = tmp_path / "skills"
    _write_skill(source_dir, "alpha")

    opencode_home = tmp_path / "opencode-home"
    monkeypatch.setenv("OPENCODE_HOME", str(opencode_home))

    result = CliRunner().invoke(
        skill_cli,
        ["install", "alpha", "--platform", "opencode", "--source", str(source_dir)],
    )

    assert result.exit_code == 0
    assert (opencode_home / "skills" / "alpha" / "SKILL.md").exists()


def test_skill_install_claude_uses_claude_home(tmp_path, monkeypatch):
    source_dir = tmp_path / "skills"
    _write_skill(source_dir, "beta")

    claude_home = tmp_path / "claude-home"
    monkeypatch.setenv("CLAUDE_HOME", str(claude_home))

    result = CliRunner().invoke(
        skill_cli,
        ["install", "beta", "--platform", "claude", "--source", str(source_dir)],
    )

    assert result.exit_code == 0
    assert (claude_home / "skills" / "beta" / "SKILL.md").exists()


def test_skill_install_overwrite_prompt_accepts_all(tmp_path, monkeypatch):
    source_dir = tmp_path / "skills"
    dest_dir = tmp_path / "dest"
    _write_skill(source_dir, "alpha")
    _write_skill(source_dir, "beta")
    _write_skill(dest_dir, "alpha")
    _write_skill(dest_dir, "beta")
    (dest_dir / "alpha" / "SKILL.md").write_text(
        "---\nname: alpha\ndescription: old alpha\n---\n\n# old\n",
        encoding="utf-8",
    )
    (dest_dir / "beta" / "SKILL.md").write_text(
        "---\nname: beta\ndescription: old beta\n---\n\n# old\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("CHATTOOL_SKILL_PLATFORM", "codex")
    monkeypatch.setattr("chattool.skill.cli.is_interactive_available", lambda: True)
    monkeypatch.setattr(
        "chattool.skill.interaction.prompt_overwrite_action", lambda skill_name: "all"
    )

    result = CliRunner().invoke(
        skill_cli,
        ["install", "--all", "--source", str(source_dir), "--dest", str(dest_dir)],
    )

    assert result.exit_code == 0
    assert "Please enter y, n, or a." not in result.output
    assert "skill alpha" in (dest_dir / "alpha" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "skill beta" in (dest_dir / "beta" / "SKILL.md").read_text(encoding="utf-8")
