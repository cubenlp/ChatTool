import shutil
import subprocess
from pathlib import Path

import click
import pytest
from click.testing import CliRunner

from chattool.client.main import cli as root_cli
from chattool.setup.playground import setup_playground


def _create_fake_chattool_repo(root: Path) -> Path:
    repo = root / "source-chattool"
    skill_dir = repo / "skills" / "demo-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: demo\nversion: 0.1.0\n---\n",
        encoding="utf-8",
    )
    (skill_dir / "SKILL.zh.md").write_text(
        "---\nname: demo-skill\ndescription: 演示\nversion: 0.1.0\n---\n",
        encoding="utf-8",
    )
    (skill_dir / "notes.txt").write_text("demo note\n", encoding="utf-8")
    return repo


def _install_fake_clone(monkeypatch, source_repo: Path) -> None:
    def fake_clone(_source, workspace_dir, force):
        repo_dir = Path(workspace_dir) / "ChatTool"
        if repo_dir.exists():
            shutil.rmtree(repo_dir)
        shutil.copytree(source_repo, repo_dir)
        return repo_dir

    def fake_update(repo_dir, chattool_source, interactive=None, can_prompt=False):
        shutil.rmtree(repo_dir)
        shutil.copytree(Path(chattool_source), repo_dir)
        return "updated"

    monkeypatch.setattr("chattool.setup.playground._clone_chattool_repo", fake_clone)
    monkeypatch.setattr("chattool.setup.playground._update_chattool_repo", fake_update)


@pytest.fixture(autouse=True)
def clear_github_token():
    from chattool.config import GitHubConfig

    original = GitHubConfig.GITHUB_ACCESS_TOKEN.value
    GitHubConfig.GITHUB_ACCESS_TOKEN.value = None
    try:
        yield
    finally:
        GitHubConfig.GITHUB_ACCESS_TOKEN.value = original


def test_setup_playground_bootstraps_workspace(tmp_path, monkeypatch):
    source_repo = _create_fake_chattool_repo(tmp_path)
    workspace = tmp_path / "workspace"
    _install_fake_clone(monkeypatch, source_repo)

    setup_playground(
        workspace_dir=workspace, chattool_source=str(source_repo), interactive=False
    )

    assert (workspace / "ChatTool").exists()
    assert not (workspace / "chattool").exists()
    assert (workspace / "AGENTS.md").exists()
    assert (workspace / "CHATTOOL.md").exists()
    assert (workspace / "MEMORY.md").exists()
    assert (workspace / "Memory" / "README.md").exists()
    assert (workspace / "Memory" / "projects.md").exists()
    assert (workspace / "Memory" / "decisions.md").exists()
    assert (workspace / "Memory" / "logs" / "README.md").exists()
    assert (workspace / "Memory" / "retros" / "README.md").exists()
    assert (workspace / "skills" / "README.md").exists()
    assert (workspace / "skills" / "demo-skill" / "SKILL.md").exists()
    assert (workspace / "skills" / "demo-skill" / "SKILL.zh.md").exists()
    assert (workspace / "skills" / "demo-skill" / "notes.txt").exists()
    assert (workspace / "skills" / "demo-skill" / "experience" / "README.md").exists()
    assert (workspace / "scratch" / "README.md").exists()

    agents = (workspace / "AGENTS.md").read_text(encoding="utf-8")
    assert "practice-make-perfact" in agents
    assert "chattool-dev-review" in agents
    assert "MEMORY.md" in agents

    memory = (workspace / "MEMORY.md").read_text(encoding="utf-8")
    assert "Must-Read Notes" in memory


def test_setup_playground_requires_empty_workspace_without_force(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "existing.txt").write_text("occupied\n", encoding="utf-8")

    try:
        setup_playground(
            workspace_dir=workspace, chattool_source="unused", interactive=False
        )
    except click.Abort:
        pass
    else:
        raise AssertionError(
            "setup_playground should abort for non-empty workspace without --force"
        )


def test_setup_playground_interactive_allows_non_empty_workspace_after_confirm(
    tmp_path, monkeypatch
):
    source_repo = _create_fake_chattool_repo(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "existing.txt").write_text("occupied\n", encoding="utf-8")
    _install_fake_clone(monkeypatch, source_repo)
    monkeypatch.setattr(
        "chattool.setup.playground.resolve_interactive_mode",
        lambda interactive, auto_prompt_condition: (None, True, False, False, False),
    )
    monkeypatch.setattr(
        "chattool.setup.playground.ask_confirm", lambda message, default=True: True
    )
    monkeypatch.setattr(
        "chattool.setup.playground.ask_text",
        lambda message, default="", password=False: "",
    )

    setup_playground(
        workspace_dir=workspace,
        chattool_source=str(source_repo),
        interactive=None,
    )

    assert (workspace / "existing.txt").read_text(encoding="utf-8") == "occupied\n"
    assert (workspace / "ChatTool").exists()
    assert (workspace / "MEMORY.md").exists()


def test_setup_playground_force_allows_existing_workspace(tmp_path, monkeypatch):
    source_repo = _create_fake_chattool_repo(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "existing.txt").write_text("keep me\n", encoding="utf-8")
    _install_fake_clone(monkeypatch, source_repo)

    setup_playground(
        workspace_dir=workspace,
        chattool_source=str(source_repo),
        interactive=False,
        force=True,
    )

    assert (workspace / "existing.txt").read_text(encoding="utf-8") == "keep me\n"
    assert (workspace / "ChatTool").exists()
    assert (workspace / "MEMORY.md").exists()


def test_setup_playground_interactive_reuses_existing_chattool_repo(
    tmp_path, monkeypatch
):
    source_repo = _create_fake_chattool_repo(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    existing_repo = workspace / "ChatTool"
    shutil.copytree(source_repo, existing_repo)
    (workspace / "existing.txt").write_text("occupied\n", encoding="utf-8")

    monkeypatch.setattr(
        "chattool.setup.playground.resolve_interactive_mode",
        lambda interactive, auto_prompt_condition: (None, True, False, False, False),
    )
    prompts = iter([True])
    monkeypatch.setattr(
        "chattool.setup.playground.ask_confirm",
        lambda message, default=True: next(prompts),
    )
    monkeypatch.setattr(
        "chattool.setup.playground.ask_text",
        lambda message, default="", password=False: "",
    )
    update_calls = []
    monkeypatch.setattr(
        "chattool.setup.playground._update_chattool_repo",
        lambda repo_dir,
        chattool_source,
        interactive=None,
        can_prompt=False: update_calls.append((repo_dir, chattool_source)) or "updated",
    )

    setup_playground(
        workspace_dir=workspace,
        chattool_source=str(source_repo),
        interactive=None,
    )

    assert (workspace / "existing.txt").read_text(encoding="utf-8") == "occupied\n"
    assert update_calls == [(existing_repo, str(source_repo))]
    assert (workspace / "ChatTool" / "skills" / "demo-skill" / "SKILL.md").exists()
    assert (workspace / "MEMORY.md").exists()


def test_setup_playground_existing_chattool_decline_skills_update_keeps_workspace_copy(
    tmp_path, monkeypatch
):
    source_repo = _create_fake_chattool_repo(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    existing_repo = workspace / "ChatTool"
    shutil.copytree(source_repo, existing_repo)
    (workspace / "existing.txt").write_text("occupied\n", encoding="utf-8")
    skill_dir = workspace / "skills" / "demo-skill"
    (skill_dir / "experience").mkdir(parents=True)
    (skill_dir / "notes.txt").write_text("workspace note\n", encoding="utf-8")
    (skill_dir / "experience" / "keep.log").write_text("keep me\n", encoding="utf-8")

    monkeypatch.setattr(
        "chattool.setup.playground.resolve_interactive_mode",
        lambda interactive, auto_prompt_condition: (None, True, False, False, False),
    )
    prompts = iter([False])
    monkeypatch.setattr(
        "chattool.setup.playground.ask_confirm",
        lambda message, default=True: next(prompts),
    )
    monkeypatch.setattr(
        "chattool.setup.playground.ask_text",
        lambda message, default="", password=False: "",
    )
    monkeypatch.setattr(
        "chattool.setup.playground._update_chattool_repo",
        lambda repo_dir, chattool_source, interactive=None, can_prompt=False: "updated",
    )

    setup_playground(
        workspace_dir=workspace,
        chattool_source=str(source_repo),
        interactive=None,
    )

    assert (skill_dir / "notes.txt").read_text(encoding="utf-8") == "workspace note\n"
    assert (skill_dir / "experience" / "keep.log").read_text(
        encoding="utf-8"
    ) == "keep me\n"


def test_root_cli_registers_setup_playground():
    runner = CliRunner()

    result = runner.invoke(root_cli, ["setup", "--help"])

    assert result.exit_code == 0
    assert "playground" in result.output


def test_root_cli_registers_setup_cc_connect():
    runner = CliRunner()

    result = runner.invoke(root_cli, ["setup", "--help"])

    assert result.exit_code == 0
    assert "cc-connect" in result.output


def test_setup_playground_configures_git_auth_from_chattool_env_value(
    tmp_path, monkeypatch
):
    source_repo = _create_fake_chattool_repo(tmp_path)
    workspace = tmp_path / "workspace"
    _install_fake_clone(monkeypatch, source_repo)

    monkeypatch.setenv("GITHUB_ACCESS_TOKEN", "env-token-should-not-win")
    from chattool.config import GitHubConfig

    GitHubConfig.GITHUB_ACCESS_TOKEN.value = "config-token-wins"

    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("chattool.setup.playground.subprocess.run", fake_run)

    setup_playground(
        workspace_dir=workspace, chattool_source=str(source_repo), interactive=False
    )

    assert ["git", "config", "--global", "credential.helper", "store"] == calls[-2][0]
    assert ["git", "credential", "approve"] == calls[-1][0]
    assert "path=cubenlp/ChatTool.git" in calls[-1][1]["input"]
    assert "password=config-token-wins" in calls[-1][1]["input"]
    assert "password=env-token-should-not-win" not in calls[-1][1]["input"]


def test_setup_playground_interactive_allows_overriding_github_token(
    tmp_path, monkeypatch
):
    source_repo = _create_fake_chattool_repo(tmp_path)
    workspace = tmp_path / "workspace"
    _install_fake_clone(monkeypatch, source_repo)

    from chattool.config import GitHubConfig

    GitHubConfig.GITHUB_ACCESS_TOKEN.value = "config-token"

    monkeypatch.setattr(
        "chattool.setup.playground.resolve_interactive_mode",
        lambda interactive, auto_prompt_condition: (None, True, False, False, False),
    )

    prompts = iter(["override-token"])
    monkeypatch.setattr(
        "chattool.setup.playground.ask_text",
        lambda message, default="", password=False: next(prompts),
    )

    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("chattool.setup.playground.subprocess.run", fake_run)

    setup_playground(
        workspace_dir=workspace, chattool_source=str(source_repo), interactive=None
    )

    assert ["git", "credential", "approve"] == calls[-1][0]
    assert "password=override-token" in calls[-1][1]["input"]


def test_setup_playground_existing_workspace_updates_skills_but_keeps_experience(
    tmp_path, monkeypatch
):
    source_repo = _create_fake_chattool_repo(tmp_path)
    workspace = tmp_path / "workspace"
    _install_fake_clone(monkeypatch, source_repo)

    setup_playground(
        workspace_dir=workspace, chattool_source=str(source_repo), interactive=False
    )

    source_skill = source_repo / "skills" / "demo-skill"
    (source_skill / "notes.txt").write_text("updated note\n", encoding="utf-8")
    experience_file = workspace / "skills" / "demo-skill" / "experience" / "keep.log"
    experience_file.write_text("keep me\n", encoding="utf-8")

    setup_playground(
        workspace_dir=workspace, chattool_source=str(source_repo), interactive=False
    )

    assert (workspace / "skills" / "demo-skill" / "notes.txt").read_text(
        encoding="utf-8"
    ) == "updated note\n"
    assert experience_file.read_text(encoding="utf-8") == "keep me\n"


def test_setup_playground_renames_legacy_chattool_dir(tmp_path, monkeypatch):
    source_repo = _create_fake_chattool_repo(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    legacy_repo = workspace / "chattool"
    shutil.copytree(source_repo, legacy_repo)

    monkeypatch.setattr(
        "chattool.setup.playground._update_chattool_repo",
        lambda repo_dir, chattool_source, interactive=None, can_prompt=False: "updated",
    )

    setup_playground(
        workspace_dir=workspace, chattool_source=str(source_repo), interactive=False
    )

    assert not legacy_repo.exists()
    assert (workspace / "ChatTool").exists()
