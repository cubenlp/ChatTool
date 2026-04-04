import os
import subprocess
import sys
from pathlib import Path


def _run_chattool_setup_workspace(args: list[str]):
    repo_root = Path(__file__).resolve().parents[2]
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


def test_setup_workspace_base_creates_scaffold(tmp_path: Path):
    workspace_dir = tmp_path / "workspace"

    result = _run_chattool_setup_workspace([str(workspace_dir), "-I"])

    assert result.returncode == 0, result.stderr
    assert (workspace_dir / "AGENTS.md").exists()
    assert (workspace_dir / "MEMORY.md").exists()
    assert (workspace_dir / "setup.md").exists()
    assert (workspace_dir / "reports" / "README.md").exists()
    assert (workspace_dir / "playgrounds" / "README.md").exists()
    assert (workspace_dir / "knowledge" / "README.md").exists()
    assert not (workspace_dir / "knowledge" / "report").exists()

    agents = (workspace_dir / "AGENTS.md").read_text(encoding="utf-8")
    setup_md = (workspace_dir / "setup.md").read_text(encoding="utf-8")
    assert "## 架构" in agents
    assert "## 知识写入规则" in agents
    assert "reports/MM-DD-<task-name>/" in agents
    assert "reports/MM-DD-<set-name>/" in agents
    assert "playgrounds/<task-name>/" in agents
    assert "playgrounds/task-sets/<set-name>/" in agents
    assert "knowledge/memory/YYYY-MM-DD-status.md" in agents
    assert "1. **Discover**" in setup_md
    assert "6. **Done**" in setup_md
    assert "Create first task lanes" in setup_md
    assert "默认创建一个常规任务" in setup_md


def test_setup_workspace_english_language_creates_english_templates(tmp_path: Path):
    workspace_dir = tmp_path / "workspace"

    result = _run_chattool_setup_workspace(
        [str(workspace_dir), "--language", "en", "-I"]
    )

    assert result.returncode == 0, result.stderr
    agents = (workspace_dir / "AGENTS.md").read_text(encoding="utf-8")
    setup_md = (workspace_dir / "setup.md").read_text(encoding="utf-8")
    assert "## Architecture" in agents
    assert "## 架构" not in agents
    assert "# Workspace Setup Checklist" in setup_md


def test_setup_workspace_force_does_not_overwrite_completed_setup_md(tmp_path: Path):
    workspace_dir = tmp_path / "workspace"

    first = _run_chattool_setup_workspace([str(workspace_dir), "-I"])
    assert first.returncode == 0, first.stderr

    setup_path = workspace_dir / "setup.md"
    original = setup_path.read_text(encoding="utf-8") + "\ncompleted: 2026-04-01\n"
    setup_path.write_text(original, encoding="utf-8")

    second = _run_chattool_setup_workspace([str(workspace_dir), "--force", "-I"])
    assert second.returncode == 0, second.stderr
    assert setup_path.read_text(encoding="utf-8") == original
