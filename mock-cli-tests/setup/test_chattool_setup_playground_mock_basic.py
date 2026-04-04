import pytest

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_setup_playground_prompts_for_missing_args(tmp_path, monkeypatch, runner):
    values = iter([str(tmp_path / "workspace"), str(tmp_path / "source")])

    def fake_text(label, default=None, **kwargs):
        return next(values)

    monkeypatch.setattr("chattool.setup.playground.ask_text", fake_text)
    monkeypatch.setattr(
        "chattool.setup.playground.resolve_interactive_mode",
        lambda interactive, auto_prompt_condition: (
            interactive,
            True,
            False,
            True,
            True,
        ),
    )
    monkeypatch.setattr(
        "chattool.setup.playground._ensure_chattool_repo",
        lambda chattool_source, workspace_dir, force, interactive, can_prompt: (
            workspace_dir / "ChatTool",
            False,
            "cloned",
        ),
    )
    monkeypatch.setattr(
        "chattool.setup.playground._update_submodules", lambda repo_dir: None
    )
    monkeypatch.setattr(
        "chattool.setup.playground._validate_cloned_repo", lambda skills_source: None
    )
    monkeypatch.setattr(
        "chattool.setup.playground._workspace_skills_source",
        lambda chattool_repo_dir: tmp_path / "skills-source",
    )
    monkeypatch.setattr(
        "chattool.setup.playground._copy_skills",
        lambda skills_source, skills_target, force, language: [],
    )
    monkeypatch.setattr(
        "chattool.setup.playground._maybe_setup_github_auth",
        lambda interactive, can_prompt: False,
    )

    result = runner.invoke(cli, ["setup", "playground"])

    assert result.exit_code == 0
    assert (tmp_path / "workspace" / "AGENTS.md").exists()
    assert (tmp_path / "workspace" / "knowledge" / "skills").exists()
    assert "Playground 初始化完成。" in result.output


def test_setup_playground_explicit_english_language(tmp_path, monkeypatch, runner):
    workspace_dir = tmp_path / "workspace"

    monkeypatch.setattr(
        "chattool.setup.playground._ensure_chattool_repo",
        lambda chattool_source, workspace_dir, force, interactive, can_prompt: (
            workspace_dir / "ChatTool",
            False,
            "cloned",
        ),
    )
    monkeypatch.setattr(
        "chattool.setup.playground._update_submodules", lambda repo_dir: None
    )
    monkeypatch.setattr(
        "chattool.setup.playground._validate_cloned_repo", lambda skills_source: None
    )
    monkeypatch.setattr(
        "chattool.setup.playground._workspace_skills_source",
        lambda chattool_repo_dir: tmp_path / "skills-source",
    )
    monkeypatch.setattr(
        "chattool.setup.playground._copy_skills",
        lambda skills_source, skills_target, force, language: [],
    )
    monkeypatch.setattr(
        "chattool.setup.playground._maybe_setup_github_auth",
        lambda interactive, can_prompt: False,
    )

    result = runner.invoke(
        cli,
        [
            "setup",
            "playground",
            "--workspace-dir",
            str(workspace_dir),
            "--chattool-source",
            str(tmp_path / "source"),
            "--language",
            "en",
            "-I",
        ],
    )

    assert result.exit_code == 0
    agents = (workspace_dir / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Overview" in agents
    assert "## 概览" not in agents
    assert "Language: en" in result.output
