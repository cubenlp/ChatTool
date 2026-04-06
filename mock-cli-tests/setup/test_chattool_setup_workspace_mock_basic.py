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

    monkeypatch.setattr("chattool.setup.workspace.cli.ask_text", fake_text)
    monkeypatch.setattr(
        "chattool.setup.workspace.options.ask_confirm",
        lambda message, default=False: False,
    )
    monkeypatch.setattr(
        "chattool.setup.workspace.cli.resolve_interactive_mode",
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
    assert (tmp_path / "workspace" / "skills").exists()
    assert (tmp_path / "workspace" / "public").exists()
    assert "Workspace 初始化完成。" in result.output


def test_setup_workspace_interactive_can_enable_chattool(tmp_path, monkeypatch, runner):
    values = iter([str(tmp_path / "workspace")])

    monkeypatch.setattr(
        "chattool.setup.workspace.cli.ask_text",
        lambda label, default=None, **kwargs: next(values),
    )
    monkeypatch.setattr(
        "chattool.setup.workspace.options.ask_confirm",
        lambda message, default=False: True,
    )
    monkeypatch.setattr(
        "chattool.setup.workspace.options.ask_checkbox_with_controls",
        lambda *args, **kwargs: ["chattool", "rexblog"],
    )
    monkeypatch.setattr(
        "chattool.setup.workspace.cli.resolve_interactive_mode",
        lambda interactive, auto_prompt_condition: (
            interactive,
            True,
            False,
            True,
            True,
        ),
    )
    monkeypatch.setattr(
        "chattool.setup.workspace.options.apply_chattool_option",
        lambda workspace_dir, source, interactive, can_prompt: {
            "name": "chattool",
            "repo_dir": workspace_dir / "core" / "ChatTool",
            "repo_action": "cloned",
            "copied_skills": ["demo-skill"],
        },
    )
    monkeypatch.setattr(
        "chattool.setup.workspace.options.apply_rexblog_option",
        lambda workspace_dir, source, interactive, can_prompt: {
            "name": "rexblog",
            "repo_dir": workspace_dir / "core" / "RexBlog",
            "repo_action": "cloned",
            "public_link": workspace_dir / "public" / "hexo_blog",
        },
    )

    result = runner.invoke(cli, ["setup", "workspace"])

    assert result.exit_code == 0
    assert "Enabled options: chattool, rexblog" in result.output


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
    assert "Current Options" in agents
    assert "已启用项" not in agents
