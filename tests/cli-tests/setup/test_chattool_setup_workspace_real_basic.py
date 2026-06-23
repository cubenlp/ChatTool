import os
import subprocess
import sys
from pathlib import Path


def _run_chattool_setup_workspace(args: list[str]):
    repo_root = Path(__file__).resolve().parents[3]
    env = os.environ.copy()
    src_dir = str(repo_root / "src")
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src_dir if not existing else f"{src_dir}:{existing}"
    return subprocess.run(
        [sys.executable, "-m", "chattool.client.main", "setup", "workspace", *args],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    subprocess.run(["git", "-C", str(path), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(path),
            "-c",
            "user.name=ChatTool Test",
            "-c",
            "user.email=chattool-test@example.invalid",
            "commit",
            "-qm",
            "initial",
        ],
        check=True,
    )


def test_setup_workspace_base_creates_scaffold(tmp_path: Path):
    workspace_dir = tmp_path / "workspace"

    result = _run_chattool_setup_workspace([str(workspace_dir), "-I"])

    assert result.returncode == 0, result.stderr
    assert not (workspace_dir / "README.md").exists()
    assert (workspace_dir / "AGENTS.md").exists()
    assert not (workspace_dir / "IDENTITY.md").exists()
    assert not (workspace_dir / "MEMORY.md").exists()
    assert (workspace_dir / "ARCHIVE.md").exists()
    assert (workspace_dir / "TODO.md").exists()
    assert (workspace_dir / ".trash").exists()
    assert (workspace_dir / "projects" / "README.md").exists()
    assert (workspace_dir / "archive" / "README.md").exists()
    assert (workspace_dir / "scripts" / "README.md").exists()
    assert not (workspace_dir / "reference" / "README.md").exists()
    assert (workspace_dir / "core").exists()
    assert (workspace_dir / "skills" / "workspace-maintenance" / "SKILL.md").exists()
    assert (workspace_dir / "skills" / "workspace-maintenance" / "SKILL.zh.md").exists()

    agents = (workspace_dir / "AGENTS.md").read_text(encoding="utf-8")
    todo = (workspace_dir / "TODO.md").read_text(encoding="utf-8")
    projects = (workspace_dir / "projects" / "README.md").read_text(encoding="utf-8")
    archive = (workspace_dir / "archive" / "README.md").read_text(encoding="utf-8")
    scripts = (workspace_dir / "scripts" / "README.md").read_text(encoding="utf-8")
    skill_zh = (workspace_dir / "skills" / "workspace-maintenance" / "SKILL.zh.md").read_text(encoding="utf-8")
    assert "## 架构" in agents
    assert "AGENTS.md" in agents
    assert "TODO.md" in agents
    assert "ARCHIVE.md" in agents
    assert "Workspace/\n  AGENTS.md\n  TODO.md\n  ARCHIVE.md" in agents
    assert "IDENTITY.md" not in agents
    assert "这里记录这个 workspace 近期打算做的事" in todo
    assert "PRD.md" in projects
    assert "reports/" in projects
    assert "topic 分组" in projects
    assert "Archive README" in archive
    assert "workspace 级维护脚本" in scripts
    assert "docs/themes" not in skill_zh
    assert "TODO.md" in skill_zh


def test_setup_workspace_english_language_creates_english_templates(tmp_path: Path):
    workspace_dir = tmp_path / "workspace"

    result = _run_chattool_setup_workspace(
        [str(workspace_dir), "--language", "en", "-I"]
    )

    assert result.returncode == 0, result.stderr
    agents = (workspace_dir / "AGENTS.md").read_text(encoding="utf-8")
    todo = (workspace_dir / "TODO.md").read_text(encoding="utf-8")
    assert "## Architecture" in agents
    assert "## 架构" not in agents
    assert "Near-term plans" in todo


def test_setup_workspace_with_chattool_syncs_repo_and_skills(tmp_path: Path):
    workspace_dir = tmp_path / "workspace"
    source_dir = Path(__file__).resolve().parents[3]

    result = _run_chattool_setup_workspace(
        [
            str(workspace_dir),
            "--with-chattool",
            "--chattool-source",
            str(source_dir),
            "-I",
        ]
    )

    assert result.returncode == 0, result.stderr
    assert (workspace_dir / "core" / "ChatTool").exists()
    assert (workspace_dir / "skills" / "practice-make-perfact").exists()
    assert (workspace_dir / "skills" / "practice-make-perfact" / "SKILL.md").exists()
    assert "ChatTool repo:" in result.stdout


def test_setup_workspace_with_chatblog_and_memory_links_assets(tmp_path: Path):
    workspace_dir = tmp_path / "workspace"
    chatblog_source = tmp_path / "ChatBlogSource"
    chatmemory_source = tmp_path / "ChatMemorySource"

    posts_dir = chatblog_source / "source" / "_posts"
    posts_dir.mkdir(parents=True)
    (posts_dir / "demo.md").write_text("# Demo\n", encoding="utf-8")
    _init_git_repo(chatblog_source)

    skill_dir = chatmemory_source / "Skills" / "chatarch" / "demo-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: demo\n---\n\n# Demo\n",
        encoding="utf-8",
    )
    _init_git_repo(chatmemory_source)

    result = _run_chattool_setup_workspace(
        [
            str(workspace_dir),
            "--with-chatblog",
            "--chatblog-source",
            str(chatblog_source),
            "--with-memory",
            "--memory-source",
            str(chatmemory_source),
            "-I",
        ]
    )

    assert result.returncode == 0, result.stderr
    assert (workspace_dir / "core" / "ChatBlog").exists()
    assert (workspace_dir / "core" / "ChatMemory").exists()
    public_link = workspace_dir / "public" / "chatblog"
    skills_link = workspace_dir / "skills" / "chatarch"
    assert public_link.is_symlink()
    assert public_link.resolve() == (
        workspace_dir / "core" / "ChatBlog" / "source" / "_posts"
    ).resolve()
    assert skills_link.is_symlink()
    assert skills_link.resolve() == (
        workspace_dir / "core" / "ChatMemory" / "Skills" / "chatarch"
    ).resolve()
    assert "ChatBlog repo:" in result.stdout
    assert "ChatMemory repo:" in result.stdout
    assert "RexBlog repo:" not in result.stdout


def test_setup_workspace_force_overwrites_generated_files(tmp_path: Path):
    workspace_dir = tmp_path / "workspace"

    first = _run_chattool_setup_workspace([str(workspace_dir), "-I"])
    assert first.returncode == 0, first.stderr

    projects_readme = workspace_dir / "projects" / "README.md"
    projects_readme.write_text("custom projects readme\n", encoding="utf-8")

    second = _run_chattool_setup_workspace([str(workspace_dir), "--force", "-I"])
    assert second.returncode == 0, second.stderr
    assert projects_readme.read_text(encoding="utf-8") != "custom projects readme\n"


def test_setup_workspace_existing_workspace_keeps_protocol_files(tmp_path: Path):
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / "AGENTS.md").write_text("legacy agents\n", encoding="utf-8")

    result = _run_chattool_setup_workspace([str(workspace_dir), "-I"])

    assert result.returncode == 0, result.stderr
    assert (workspace_dir / "AGENTS.md").read_text(encoding="utf-8") == "legacy agents\n"
    assert not (workspace_dir / "README.md").exists()
    assert not (workspace_dir / "IDENTITY.md").exists()
