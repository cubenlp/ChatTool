import shutil
from pathlib import Path

import click
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
    def fake_clone(_source, workspace_dir, force, interactive=None, can_prompt=False):
        repo_dir = Path(workspace_dir) / "chattool"
        if repo_dir.exists():
            shutil.rmtree(repo_dir)
        shutil.copytree(source_repo, repo_dir)
        return repo_dir

    monkeypatch.setattr("chattool.setup.playground._clone_chattool_repo", fake_clone)


def test_setup_playground_bootstraps_workspace(tmp_path, monkeypatch):
    source_repo = _create_fake_chattool_repo(tmp_path)
    workspace = tmp_path / "workspace"
    _install_fake_clone(monkeypatch, source_repo)

    setup_playground(workspace_dir=workspace, chattool_source=str(source_repo), interactive=False)

    assert (workspace / "chattool").exists()
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
        setup_playground(workspace_dir=workspace, chattool_source="unused", interactive=False)
    except click.Abort:
        pass
    else:
        raise AssertionError("setup_playground should abort for non-empty workspace without --force")


def test_setup_playground_interactive_allows_non_empty_workspace_after_confirm(tmp_path, monkeypatch):
    source_repo = _create_fake_chattool_repo(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "existing.txt").write_text("occupied\n", encoding="utf-8")
    _install_fake_clone(monkeypatch, source_repo)
    monkeypatch.setattr(
        "chattool.setup.playground.resolve_interactive_mode",
        lambda interactive, auto_prompt_condition: (None, True, False, False, False),
    )
    monkeypatch.setattr("chattool.setup.playground.ask_confirm", lambda message, default=True: True)

    setup_playground(
        workspace_dir=workspace,
        chattool_source=str(source_repo),
        interactive=None,
    )

    assert (workspace / "existing.txt").read_text(encoding="utf-8") == "occupied\n"
    assert (workspace / "chattool").exists()
    assert (workspace / "MEMORY.md").exists()


def test_setup_playground_force_allows_existing_workspace(tmp_path, monkeypatch):
    source_repo = _create_fake_chattool_repo(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "existing.txt").write_text("keep me\n", encoding="utf-8")
    _install_fake_clone(monkeypatch, source_repo)

    setup_playground(workspace_dir=workspace, chattool_source=str(source_repo), interactive=False, force=True)

    assert (workspace / "existing.txt").read_text(encoding="utf-8") == "keep me\n"
    assert (workspace / "chattool").exists()
    assert (workspace / "MEMORY.md").exists()


def test_setup_playground_interactive_reuses_existing_chattool_repo(tmp_path, monkeypatch):
    source_repo = _create_fake_chattool_repo(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    existing_repo = workspace / "chattool"
    shutil.copytree(source_repo, existing_repo)
    (workspace / "existing.txt").write_text("occupied\n", encoding="utf-8")

    monkeypatch.setattr(
        "chattool.setup.playground.resolve_interactive_mode",
        lambda interactive, auto_prompt_condition: (None, True, False, False, False),
    )
    prompts = iter([True, True])
    monkeypatch.setattr("chattool.setup.playground.ask_confirm", lambda message, default=True: next(prompts))

    setup_playground(
        workspace_dir=workspace,
        chattool_source=str(source_repo),
        interactive=None,
    )

    assert (workspace / "existing.txt").read_text(encoding="utf-8") == "occupied\n"
    assert (workspace / "chattool" / "skills" / "demo-skill" / "SKILL.md").exists()
    assert (workspace / "MEMORY.md").exists()


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
