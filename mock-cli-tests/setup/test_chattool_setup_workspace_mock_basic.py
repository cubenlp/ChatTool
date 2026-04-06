from pathlib import Path

import pytest

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_setup_workspace_prompts_for_missing_profile_and_dir(
    tmp_path, monkeypatch, runner
):
    selected: dict[str, str | None] = {"workspace": None}

    def fake_text(label, default=None, **kwargs):
        selected["workspace"] = str(tmp_path / "workspace")
        return selected["workspace"]

    monkeypatch.setattr("chattool.setup.workspace.ask_text", fake_text)
    monkeypatch.setattr(
        "chattool.setup.workspace.ask_confirm", lambda message, default=False: False
    )
    monkeypatch.setattr(
        "chattool.setup.workspace.resolve_interactive_mode",
        lambda interactive, auto_prompt_condition: (
            interactive,
            True,
            False,
            True,
            True,
        ),
    )

    result = runner.invoke(cli, ["setup", "workspace"])

    assert result.exit_code == 0
    assert selected["workspace"] is not None
    assert (tmp_path / "workspace" / "core").exists()
    assert (tmp_path / "workspace" / "reference").exists()
    assert (tmp_path / "workspace" / "docs" / "skills").exists()
    assert "Workspace 初始化完成。" in result.output


def test_setup_workspace_interactive_can_enable_chattool(tmp_path, monkeypatch, runner):
    values = iter([str(tmp_path / "workspace"), str(tmp_path / "source")])

    monkeypatch.setattr(
        "chattool.setup.workspace.ask_text",
        lambda label, default=None, **kwargs: next(values),
    )
    monkeypatch.setattr(
        "chattool.setup.workspace.ask_confirm", lambda message, default=False: True
    )
    monkeypatch.setattr(
        "chattool.setup.workspace.resolve_interactive_mode",
        lambda interactive, auto_prompt_condition: (
            interactive,
            True,
            False,
            True,
            True,
        ),
    )
    monkeypatch.setattr(
        "chattool.setup.workspace._ensure_chattool_repo",
        lambda chattool_source, workspace_dir, force, interactive, can_prompt: (
            workspace_dir / "ChatTool",
            False,
            "cloned",
        ),
    )
    monkeypatch.setattr(
        "chattool.setup.workspace._workspace_skills_source",
        lambda repo_dir: tmp_path / "skills-source",
    )
    monkeypatch.setattr(
        "chattool.setup.workspace._validate_cloned_repo", lambda skills_source: None
    )
    monkeypatch.setattr(
        "chattool.setup.workspace._copy_skills",
        lambda skills_source, skills_target, force, language: ["demo-skill"],
    )
    monkeypatch.setattr(
        "chattool.setup.workspace._maybe_setup_github_auth",
        lambda interactive, can_prompt: False,
    )

    result = runner.invoke(cli, ["setup", "workspace"])

    assert result.exit_code == 0
    assert "With ChatTool: True" in result.output


def test_setup_workspace_dry_run_writes_nothing(tmp_path, runner):
    workspace_dir = tmp_path / "workspace"

    result = runner.invoke(
        cli,
        ["setup", "workspace", str(workspace_dir), "--dry-run", "-I"],
    )

    assert result.exit_code == 0
    assert "Workspace 初始化预演。" in result.output
    assert not workspace_dir.exists()


def test_setup_workspace_explicit_english_language(tmp_path, runner):
    workspace_dir = tmp_path / "workspace"

    result = runner.invoke(
        cli,
        ["setup", "workspace", str(workspace_dir), "--language", "en", "-I"],
    )

    assert result.exit_code == 0
    agents = (workspace_dir / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Architecture" in agents
    assert "## 架构" not in agents
