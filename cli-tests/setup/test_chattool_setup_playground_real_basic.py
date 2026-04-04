import os
import subprocess
import sys
from pathlib import Path


def _run_chattool_setup_playground(args: list[str]):
    repo_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    src_dir = str(repo_root / "src")
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src_dir if not existing else f"{src_dir}:{existing}"
    return subprocess.run(
        [sys.executable, "-m", "chattool.client.main", "setup", "playground", *args],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def test_setup_playground_creates_workspace_style_scaffold(tmp_path: Path):
    workspace_dir = tmp_path / "playground"
    source_dir = Path(__file__).resolve().parents[2]

    result = _run_chattool_setup_playground(
        [
            "--workspace-dir",
            str(workspace_dir),
            "--chattool-source",
            str(source_dir),
            "-I",
        ]
    )

    assert result.returncode == 0, result.stderr
    assert (workspace_dir / "AGENTS.md").exists()
    assert (workspace_dir / "CHATTOOL.md").exists()
    assert (workspace_dir / "MEMORY.md").exists()
    assert (workspace_dir / "reports" / "README.md").exists()
    assert (workspace_dir / "playgrounds" / "README.md").exists()
    assert (workspace_dir / "playgrounds" / "scratch" / "README.md").exists()
    assert (workspace_dir / "knowledge" / "README.md").exists()
    assert (workspace_dir / "knowledge" / "memory" / "README.md").exists()
    assert (workspace_dir / "knowledge" / "skills" / "README.md").exists()
    assert (workspace_dir / "ChatTool").exists()

    assert not (workspace_dir / "Memory").exists()
    assert not (workspace_dir / "skills").exists()
    assert not (workspace_dir / "scratch").exists()

    agents = (workspace_dir / "AGENTS.md").read_text(encoding="utf-8")
    chattool_md = (workspace_dir / "CHATTOOL.md").read_text(encoding="utf-8")
    memory_md = (workspace_dir / "MEMORY.md").read_text(encoding="utf-8")
    assert "## 概览" in agents
    assert "reports/MM-DD-<task-name>/" in agents
    assert "reports/task-sets/<set-name>/" in agents
    assert "knowledge/skills/" in agents
    assert "ChatTool Workspace 指南" in chattool_md
    assert "长期笔记目录" in memory_md

    copied_skill = workspace_dir / "knowledge" / "skills" / "practice-make-perfact"
    assert copied_skill.exists()
    assert (copied_skill / "experience" / "README.md").exists()


def test_setup_playground_english_language_creates_english_templates(tmp_path: Path):
    workspace_dir = tmp_path / "playground-en"
    source_dir = Path(__file__).resolve().parents[2]

    result = _run_chattool_setup_playground(
        [
            "--workspace-dir",
            str(workspace_dir),
            "--chattool-source",
            str(source_dir),
            "--language",
            "en",
            "-I",
        ]
    )

    assert result.returncode == 0, result.stderr
    agents = (workspace_dir / "AGENTS.md").read_text(encoding="utf-8")
    chattool_md = (workspace_dir / "CHATTOOL.md").read_text(encoding="utf-8")
    memory_md = (workspace_dir / "MEMORY.md").read_text(encoding="utf-8")
    assert "## Overview" in agents
    assert "## 概览" not in agents
    assert "# ChatTool Workspace Guide" in chattool_md
    assert "# ChatTool Workspace 指南" not in chattool_md
    assert "## Must-Read Notes" in memory_md
    assert "## 必读事项" not in memory_md
    assert "Language: en" in result.stdout
