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


def test_setup_workspace_base_creates_scaffold(tmp_path: Path):
    workspace_dir = tmp_path / "workspace"

    result = _run_chattool_setup_workspace([str(workspace_dir), "-I"])

    assert result.returncode == 0, result.stderr
    assert (workspace_dir / "AGENTS.md").exists()
    assert (workspace_dir / "MEMORY.md").exists()
    assert (workspace_dir / "setup.md").exists()
    assert (workspace_dir / "core").exists()
    assert (workspace_dir / "reference").exists()
    assert (workspace_dir / "reports" / "README.md").exists()
    assert (workspace_dir / "playgrounds" / "README.md").exists()
    assert (workspace_dir / "docs" / "README.md").exists()
    assert (workspace_dir / "docs" / "memory" / "README.md").exists()
    assert (workspace_dir / "docs" / "skills" / "README.md").exists()
    assert (workspace_dir / "docs" / "tools" / "README.md").exists()

    agents = (workspace_dir / "AGENTS.md").read_text(encoding="utf-8")
    memory = (workspace_dir / "MEMORY.md").read_text(encoding="utf-8")
    setup_md = (workspace_dir / "setup.md").read_text(encoding="utf-8")
    assert "## 架构" in agents
    assert "## 写入规则" in agents
    assert "- 任务分为 `task` 和 `taskset`，默认使用 `task`。" in agents
    assert (
        "- 任务未完成前不要阶段性邀请 review；默认完整做完后再统一汇报结果。" in agents
    )
    assert (
        "- 如果是开发任务，每个阶段都要先测试通过、文档完善，并自行 review 后再继续。"
        in agents
    )
    assert "reports/MM-DD-<task-name>/" in agents
    assert "reports/MM-DD-<set-name>/" in agents
    assert "playgrounds/<task-name>/" in agents
    assert "playgrounds/task-sets/<set-name>/" in agents
    assert "docs/memory/YYYY-MM-DD-status.md" in agents
    assert "core/" in agents
    assert "reference/" in agents
    assert "docs/" in agents
    assert "## 当前 Workspace" in memory
    assert "- 核心仓库目录：`core/`" in memory
    assert "- 参考资料目录：`reference/`" in memory
    assert "- 持久状态记录目录：`docs/memory/`" in memory
    assert "- 技能沉淀目录：`docs/skills/`" in memory
    assert "## 启动清单" in setup_md
    assert "1. Discover" in setup_md
    assert "6. Done" in setup_md
    assert "默认完整做完后再统一汇报结果" in setup_md


def test_setup_workspace_english_language_creates_english_templates(tmp_path: Path):
    workspace_dir = tmp_path / "workspace"

    result = _run_chattool_setup_workspace(
        [str(workspace_dir), "--language", "en", "-I"]
    )

    assert result.returncode == 0, result.stderr
    agents = (workspace_dir / "AGENTS.md").read_text(encoding="utf-8")
    memory = (workspace_dir / "MEMORY.md").read_text(encoding="utf-8")
    setup_md = (workspace_dir / "setup.md").read_text(encoding="utf-8")
    assert "## Architecture" in agents
    assert "## 架构" not in agents
    assert "## Current Workspace" in memory
    assert "## Startup Checklist" in setup_md


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


def test_setup_workspace_force_overwrites_generated_files(tmp_path: Path):
    workspace_dir = tmp_path / "workspace"

    first = _run_chattool_setup_workspace([str(workspace_dir), "-I"])
    assert first.returncode == 0, first.stderr

    reports_readme = workspace_dir / "reports" / "README.md"
    reports_readme.write_text("custom reports readme\n", encoding="utf-8")

    second = _run_chattool_setup_workspace([str(workspace_dir), "--force", "-I"])
    assert second.returncode == 0, second.stderr
    assert reports_readme.read_text(encoding="utf-8") != "custom reports readme\n"


def test_setup_workspace_existing_workspace_writes_migration_helpers(tmp_path: Path):
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / "AGENTS.md").write_text("legacy agents\n", encoding="utf-8")
    (workspace_dir / "MEMORY.md").write_text("legacy memory\n", encoding="utf-8")

    result = _run_chattool_setup_workspace([str(workspace_dir), "-I"])

    assert result.returncode == 0, result.stderr
    assert (workspace_dir / "AGENTS.md").read_text(
        encoding="utf-8"
    ) == "legacy agents\n"
    assert (workspace_dir / "MEMORY.md").read_text(
        encoding="utf-8"
    ) == "legacy memory\n"
    assert (workspace_dir / "AGENTS.generated.md").exists()
    assert (workspace_dir / "MEMORY.generated.md").exists()
    setup_md = (workspace_dir / "setup.md").read_text(encoding="utf-8")
    assert "## 迁移清单" in setup_md
    assert "AGENTS.generated.md" in setup_md
    assert "MEMORY.generated.md" in setup_md


def test_setup_workspace_completed_setup_md_is_not_overwritten(tmp_path: Path):
    workspace_dir = tmp_path / "workspace"

    first = _run_chattool_setup_workspace([str(workspace_dir), "-I"])
    assert first.returncode == 0, first.stderr

    setup_md = workspace_dir / "setup.md"
    original = setup_md.read_text(encoding="utf-8")
    locked = original + "\ncompleted: 2026-04-10\n"
    setup_md.write_text(locked, encoding="utf-8")

    second = _run_chattool_setup_workspace([str(workspace_dir), "--force", "-I"])
    assert second.returncode == 0, second.stderr
    assert setup_md.read_text(encoding="utf-8") == locked
