from pathlib import Path

import pytest

from chattool.client.main import cli
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
        lambda *args, **kwargs: ["chattool", "rexblog", "memory"],
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
    monkeypatch.setattr(
        "chattool.setup.workspace.options.apply_memory_option",
        lambda workspace_dir, source, interactive, can_prompt: {
            "name": "memory",
            "repo_dir": workspace_dir / "core" / "ChatMemory",
            "repo_action": "cloned",
            "linked_groups": ["common", "chatarch"],
            "skipped_groups": [],
        },
    )

    result = runner.invoke(cli, ["setup", "workspace"])

    assert result.exit_code == 0
    assert "Enabled options: chattool, rexblog, memory" in result.output
    assert "ChatMemory repo:" in result.output
    assert "Linked memory skill groups: common, chatarch" in result.output


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
    assert (workspace_dir / "archive" / "index.md").exists()
    assert not (workspace_dir / "archive" / "README.md").exists()
    assert (workspace_dir / "scripts" / "README.md").exists()
    assert not (workspace_dir / "README.md").exists()
    agents = (workspace_dir / "AGENTS.md").read_text(encoding="utf-8")
    archive_guide = (workspace_dir / "ARCHIVE.md").read_text(encoding="utf-8")
    archive_index = (workspace_dir / "archive" / "index.md").read_text(encoding="utf-8")
    todo = (workspace_dir / "TODO.md").read_text(encoding="utf-8")
    assert "projects/" in agents
    assert "archive/" in agents
    assert "scripts/" in agents
    assert "Workspace/\n  AGENTS.md\n  TODO.md\n  ARCHIVE.md" in agents
    assert "归档操作指南" in archive_guide
    assert "已归档内容索引" in archive_index
    assert "近期打算做的事" in todo


def test_setup_workspace_existing_workspace_keeps_protocol_files(tmp_path, runner):
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / "AGENTS.md").write_text("legacy agents\n", encoding="utf-8")

    result = runner.invoke(cli, ["setup", "workspace", str(workspace_dir), "-I"])

    assert result.exit_code == 0
    assert (workspace_dir / "AGENTS.md").read_text(encoding="utf-8") == "legacy agents\n"
    assert not (workspace_dir / "README.md").exists()


def test_memory_option_links_only_default_shared_groups(tmp_path, monkeypatch):
    from chattool.setup.workspace.options import apply_memory_option

    workspace_dir = tmp_path / "workspace"
    memory_dir = workspace_dir / "core" / "ChatMemory"

    def fake_clone(source, repo_dir, interactive, can_prompt):
        assert repo_dir == memory_dir
        for group in ["common", "chatarch", "prd-task", "machine"]:
            skill = repo_dir / "Skills" / group / "demo" / "SKILL.md"
            skill.parent.mkdir(parents=True, exist_ok=True)
            skill.write_text(f"# {group}\n", encoding="utf-8")
        return "cloned"

    monkeypatch.setattr(
        "chattool.setup.workspace.options._clone_or_update_repo", fake_clone
    )

    result = apply_memory_option(workspace_dir, "https://example.invalid/repo.git", False, False)

    assert result["linked_groups"] == ["common", "chatarch"]
    assert result["skipped_groups"] == []
    assert (workspace_dir / "skills" / "common").is_symlink()
    assert (workspace_dir / "skills" / "chatarch").is_symlink()
    assert not (workspace_dir / "skills" / "prd-task").exists()
    assert not (workspace_dir / "skills" / "machine").exists()


def test_memory_option_skips_missing_allowlist_group(tmp_path, monkeypatch):
    from chattool.setup.workspace.options import apply_memory_option

    workspace_dir = tmp_path / "workspace"

    def fake_clone(source, repo_dir, interactive, can_prompt):
        skill = repo_dir / "Skills" / "chatarch" / "demo" / "SKILL.md"
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_text("# chatarch\n", encoding="utf-8")
        return "cloned"

    monkeypatch.setattr(
        "chattool.setup.workspace.options._clone_or_update_repo", fake_clone
    )

    result = apply_memory_option(workspace_dir, "https://example.invalid/repo.git", False, False)

    assert result["linked_groups"] == ["chatarch"]
    assert result["skipped_groups"] == ["common"]
    assert not (workspace_dir / "skills" / "common").exists()
    assert (workspace_dir / "skills" / "chatarch").is_symlink()


def test_memory_option_refuses_to_replace_existing_non_symlink_group(tmp_path, monkeypatch):
    from chattool.setup.workspace.options import apply_memory_option

    workspace_dir = tmp_path / "workspace"
    existing_common = workspace_dir / "skills" / "common"
    existing_common.mkdir(parents=True)
    (existing_common / "KEEP.md").write_text("keep\n", encoding="utf-8")

    def fake_clone(source, repo_dir, interactive, can_prompt):
        skill = repo_dir / "Skills" / "common" / "demo" / "SKILL.md"
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_text("# common\n", encoding="utf-8")
        return "cloned"

    monkeypatch.setattr(
        "chattool.setup.workspace.options._clone_or_update_repo", fake_clone
    )

    with pytest.raises(Exception, match="Refusing to replace existing non-symlink path"):
        apply_memory_option(workspace_dir, "https://example.invalid/repo.git", False, False)
