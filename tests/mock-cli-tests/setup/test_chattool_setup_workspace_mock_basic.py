from pathlib import Path

import pytest

from chattool.client.main import cli
from chattool.setup.workspace.render import render_agents_md, render_memory_md, render_projects_readme, render_root_readme


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
    assert (tmp_path / "workspace" / "skills").exists()
    assert (tmp_path / "workspace" / "public").exists()
    assert (tmp_path / "workspace" / "README.md").exists()
    assert "Workspace 初始化完成。" in result.output


def test_workspace_template_variants_can_be_loaded():
    assert "Workspace" in render_root_readme("en", template_variant="default")
    assert "Workspace" in render_root_readme("en", template_variant="opencode-loop")
    assert "Projects" in render_projects_readme("en", template_variant="default")
    assert "Projects" in render_projects_readme("en", template_variant="opencode-loop")
    assert "项目根目录" in render_memory_md("zh", template_variant="default")
    assert "项目根目录" in render_memory_md("zh", template_variant="opencode-loop")
    assert "已启用项" in render_agents_md(
        Path("/tmp/demo"),
        profile=type("P", (), {"extra_files": lambda self, workspace_dir: {}})(),
        language="zh",
        enabled_options=["opencode_loop"],
        template_variant="opencode-loop",
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
    prompts = []
    monkeypatch.setattr(
        "chattool.setup.workspace.options.ask_text",
        lambda label, default="", password=False, style=None: (
            prompts.append(label),
            default,
        )[1],
    )
    monkeypatch.setattr(
        "chattool.setup.workspace.options._read_current_repo_github_token",
        lambda: "github_pat_existing_token",
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
        lambda workspace_dir, source, interactive, can_prompt, github_token=None: {
            "name": "chattool",
            "repo_dir": workspace_dir / "core" / "ChatTool",
            "repo_action": "cloned",
            "copied_skills": ["demo-skill"],
        },
    )
    monkeypatch.setattr(
        "chattool.setup.workspace.options.apply_rexblog_option",
        lambda workspace_dir, source, interactive, can_prompt, github_token=None: {
            "name": "rexblog",
            "repo_dir": workspace_dir / "core" / "RexBlog",
            "repo_action": "cloned",
            "public_link": workspace_dir / "public" / "hexo_blog",
        },
    )

    result = runner.invoke(cli, ["setup", "workspace"])

    assert result.exit_code == 0
    assert "Enabled options: chattool, rexblog" in result.output
    assert any("ChatTool github_token" in item for item in prompts)
    assert any("RexBlog github_token" in item for item in prompts)
    assert any(("当前" in item) or ("current" in item) for item in prompts)


def test_setup_workspace_interactive_configures_repo_tokens(
    tmp_path, monkeypatch, runner
):
    values = iter([str(tmp_path / "workspace")])
    configured = []

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
        "chattool.setup.workspace.options._read_current_repo_github_token",
        lambda: "github_pat_existing_token",
    )
    monkeypatch.setattr(
        "chattool.setup.workspace.options.ask_text",
        lambda label, default="", password=False, style=None: default,
    )
    monkeypatch.setattr(
        "chattool.setup.workspace.options.apply_chattool_option",
        lambda workspace_dir, source, interactive, can_prompt, github_token=None: (
            configured.append((source, github_token)),
            {
                "name": "chattool",
                "repo_dir": workspace_dir / "core" / "ChatTool",
                "repo_action": "cloned",
                "copied_skills": ["demo-skill"],
            },
        )[1],
    )
    monkeypatch.setattr(
        "chattool.setup.workspace.options.apply_rexblog_option",
        lambda workspace_dir, source, interactive, can_prompt, github_token=None: (
            configured.append((source, github_token)),
            {
                "name": "rexblog",
                "repo_dir": workspace_dir / "core" / "RexBlog",
                "repo_action": "cloned",
                "public_link": workspace_dir / "public" / "hexo_blog",
            },
        )[1],
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
    assert (
        "https://github.com/cubenlp/ChatTool.git",
        "github_pat_existing_token",
    ) in configured
    assert (
        "https://github.com/RexWzh/RexBlog",
        "github_pat_existing_token",
    ) in configured


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
    readme = (workspace_dir / "README.md").read_text(encoding="utf-8")
    assert "Current Options" in agents
    assert "已启用项" not in agents
    assert "Human-AI collaboration workspace root." in readme


def test_setup_workspace_uses_projects_model(tmp_path, runner):
    workspace_dir = tmp_path / "workspace"

    result = runner.invoke(cli, ["setup", "workspace", str(workspace_dir), "-I"])

    assert result.exit_code == 0
    assert (workspace_dir / "projects" / "README.md").exists()
    assert not (workspace_dir / "reports" / "README.md").exists()
    assert not (workspace_dir / "playgrounds" / "README.md").exists()
    agents = (workspace_dir / "AGENTS.md").read_text(encoding="utf-8")
    memory = (workspace_dir / "MEMORY.md").read_text(encoding="utf-8")
    assert "projects/" in agents
    assert "reports/" not in agents
    assert "projects/" in memory
    assert "reference/" not in memory


def test_setup_workspace_existing_workspace_keeps_protocol_files(tmp_path, runner):
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / "AGENTS.md").write_text("legacy agents\n", encoding="utf-8")
    (workspace_dir / "MEMORY.md").write_text("legacy memory\n", encoding="utf-8")

    result = runner.invoke(cli, ["setup", "workspace", str(workspace_dir), "-I"])

    assert result.exit_code == 0
    assert not (workspace_dir / "AGENTS.generated.md").exists()
    assert not (workspace_dir / "MEMORY.generated.md").exists()
    assert (workspace_dir / "README.md").exists()
    assert (workspace_dir / "AGENTS.md").read_text(
        encoding="utf-8"
    ) == "legacy agents\n"


def test_setup_workspace_with_opencode_loop_installs_local_assets(
    tmp_path, monkeypatch, runner
):
    workspace_dir = tmp_path / "workspace"
    opencode_home = tmp_path / "opencode-home"

    monkeypatch.setenv("OPENCODE_HOME", str(opencode_home))
    monkeypatch.setattr(
        "chattool.setup.opencode.ensure_nodejs_requirement",
        lambda interactive, can_prompt, log_level="INFO": None,
    )
    monkeypatch.setattr(
        "chattool.setup.opencode.should_install_global_npm_package",
        lambda *args, **kwargs: False,
    )

    result = runner.invoke(
        cli,
        [
            "setup",
            "workspace",
            str(workspace_dir),
            "-I",
            "--with-opencode-loop",
        ],
    )

    assert result.exit_code == 0
    assert not (workspace_dir / ".opencode" / "opencode.jsonc").exists()
    assert (opencode_home / "plugins" / "chatloop" / "index.ts").exists()
    assert (opencode_home / "command" / "chatloop.md").exists()
    assert (opencode_home / "command" / "chatloop-status.md").exists()
    config = (opencode_home / "opencode.json").read_text(encoding="utf-8")
    assert str((opencode_home / "plugins" / "chatloop" / "index.ts").resolve()) in config
    agents = (workspace_dir / "AGENTS.md").read_text(encoding="utf-8")
    readme = (workspace_dir / "README.md").read_text(encoding="utf-8")
    memory = (workspace_dir / "MEMORY.md").read_text(encoding="utf-8")
    assert "当前 workspace 已启用 OpenCode loop-aware 模式" in agents
    assert "显式触发 `/chatloop ...`" in readme
    assert "项目根目录：`projects/`" in memory
    assert "OpenCode home:" in result.output
