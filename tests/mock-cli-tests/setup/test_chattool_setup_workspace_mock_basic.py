from pathlib import Path

import click
import pytest

from chattool.client.main import cli
from chattool.setup.workspace import options as workspace_options
from chattool.setup.workspace.render import render_agents_md, render_projects_readme


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
    assert (tmp_path / "workspace" / "projects").exists()
    assert (tmp_path / "workspace" / "archive").exists()
    assert (tmp_path / "workspace" / "scripts").exists()
    assert (tmp_path / "workspace" / "skills").exists()
    assert (tmp_path / "workspace" / "public").exists()
    assert (tmp_path / "workspace" / ".trash").exists()
    assert not (tmp_path / "workspace" / "README.md").exists()
    assert "Workspace 初始化完成。" in result.output


def test_workspace_templates_can_be_loaded():
    assert "Projects" in render_projects_readme("en")
    assert "已启用项" in render_agents_md(
        Path("/tmp/demo"),
        profile=type("P", (), {"extra_files": lambda self, workspace_dir: {}})(),
        language="zh",
        enabled_options=[],
    )


def test_setup_workspace_interactive_can_enable_chattool_chatblog_memory(
    tmp_path, monkeypatch, runner
):
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
        lambda *args, **kwargs: ["chattool", "chatblog", "memory"],
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
        "chattool.setup.workspace.options.apply_chatblog_option",
        lambda workspace_dir, source, interactive, can_prompt: {
            "name": "chatblog",
            "repo_dir": workspace_dir / "core" / "ChatBlog",
            "repo_action": "cloned",
            "public_link": workspace_dir / "public" / "chatblog",
        },
        raising=False,
    )
    monkeypatch.setattr(
        "chattool.setup.workspace.options.apply_memory_option",
        lambda workspace_dir, source, interactive, can_prompt: {
            "name": "memory",
            "repo_dir": workspace_dir / "core" / "ChatMemory",
            "repo_action": "cloned",
            "skills_link": workspace_dir / "skills" / "chatarch",
            "skipped": False,
        },
        raising=False,
    )

    result = runner.invoke(cli, ["setup", "workspace"])

    assert result.exit_code == 0
    assert "Enabled options: chattool, chatblog, memory" in result.output
    assert "ChatBlog repo:" in result.output
    assert "ChatMemory repo:" in result.output
    assert "RexBlog repo:" not in result.output


def test_setup_workspace_memory_option_skips_without_clone_permission(
    tmp_path, monkeypatch, runner
):
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
        lambda *args, **kwargs: ["memory"],
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
        "chattool.setup.workspace.options._clone_or_update_repo",
        lambda *args, **kwargs: (_ for _ in ()).throw(click.ClickException("no clone permission")),
    )

    result = runner.invoke(cli, ["setup", "workspace"])

    assert result.exit_code == 0
    assert "Enabled options: memory" in result.output
    assert "ChatMemory skipped: no clone permission" in result.output
    assert not (tmp_path / "workspace" / "skills" / "chatarch").exists()


def test_memory_option_refuses_to_replace_existing_chatarch_directory(
    tmp_path, monkeypatch
):
    workspace_dir = tmp_path / "workspace"
    existing_chatarch = workspace_dir / "skills" / "chatarch"
    existing_chatarch.mkdir(parents=True)
    marker = existing_chatarch / "KEEP.md"
    marker.write_text("keep me\n", encoding="utf-8")

    fake_memory = tmp_path / "ChatMemory"
    (fake_memory / "Skills" / "chatarch").mkdir(parents=True)

    def fake_clone(source, repo_dir, interactive, can_prompt):
        (repo_dir / "Skills" / "chatarch").mkdir(parents=True)
        return "updated"

    monkeypatch.setattr(
        workspace_options,
        "_clone_or_update_repo",
        fake_clone,
    )
    monkeypatch.setattr(
        workspace_options,
        "CHATMEMORY_REPO_URL",
        str(fake_memory),
    )

    with pytest.raises(click.ClickException, match="Refusing to replace"):
        workspace_options.apply_memory_option(
            workspace_dir,
            str(fake_memory),
            interactive=False,
            can_prompt=False,
        )

    assert existing_chatarch.is_dir()
    assert marker.read_text(encoding="utf-8") == "keep me\n"


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
    todo = (workspace_dir / "TODO.md").read_text(encoding="utf-8")
    assert "Current Options" in agents
    assert "已启用项" not in agents
    assert "Near-term plans" in todo


def test_setup_workspace_uses_current_workspace_model(tmp_path, runner):
    workspace_dir = tmp_path / "workspace"

    result = runner.invoke(cli, ["setup", "workspace", str(workspace_dir), "-I"])

    assert result.exit_code == 0
    assert (workspace_dir / "projects" / "README.md").exists()
    assert (workspace_dir / "archive" / "README.md").exists()
    assert (workspace_dir / "scripts" / "README.md").exists()
    assert not (workspace_dir / "README.md").exists()
    agents = (workspace_dir / "AGENTS.md").read_text(encoding="utf-8")
    archive = (workspace_dir / "archive" / "README.md").read_text(encoding="utf-8")
    todo = (workspace_dir / "TODO.md").read_text(encoding="utf-8")
    assert "projects/" in agents
    assert "archive/" in agents
    assert "scripts/" in agents
    assert "Workspace/\n  AGENTS.md\n  TODO.md\n  ARCHIVE.md" in agents
    assert "归档日期" in archive
    assert "近期打算做的事" in todo


def test_setup_workspace_existing_workspace_keeps_protocol_files(tmp_path, runner):
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / "AGENTS.md").write_text("legacy agents\n", encoding="utf-8")

    result = runner.invoke(cli, ["setup", "workspace", str(workspace_dir), "-I"])

    assert result.exit_code == 0
    assert (workspace_dir / "AGENTS.md").read_text(encoding="utf-8") == "legacy agents\n"
    assert not (workspace_dir / "README.md").exists()
