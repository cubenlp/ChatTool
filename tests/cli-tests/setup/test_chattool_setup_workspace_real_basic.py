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
    assert (workspace_dir / "README.md").exists()
    assert (workspace_dir / "AGENTS.md").exists()
    assert (workspace_dir / "MEMORY.md").exists()
    assert (workspace_dir / "projects" / "README.md").exists()
    assert (workspace_dir / "core").exists()
    assert (workspace_dir / "docs" / "README.md").exists()
    assert (workspace_dir / "docs" / "memory" / "README.md").exists()
    assert (workspace_dir / "docs" / "skills" / "README.md").exists()
    assert (workspace_dir / "docs" / "tools" / "README.md").exists()

    readme = (workspace_dir / "README.md").read_text(encoding="utf-8")
    agents = (workspace_dir / "AGENTS.md").read_text(encoding="utf-8")
    memory = (workspace_dir / "MEMORY.md").read_text(encoding="utf-8")
    assert "## 架构" in agents
    assert "## 写入规则" in agents
    assert "- 所有实际工作统一放到 `projects/` 下。" in agents
    assert (
        "- review 由 loop 在模型准备停下时触发；默认完整做完后再统一汇报结果。"
        in agents
    )
    assert (
        "- 如果是开发任务，每个阶段都要先测试通过、文档完善，再根据 `review.md` 定义的规则做校验与验收收尾。"
        in agents
    )
    assert "projects/MM-DD-<task-name>/" in agents
    assert "projects/MM-DD-<project-name>/" in agents
    assert "tasks/<task-name>/" in agents
    assert "docs/memory/YYYY-MM-DD-status.md" in agents
    assert "core/" in agents
    assert "docs/" in agents
    assert "`projects/` 作为实际工作的执行容器" in readme
    assert "## 当前 Workspace" in memory
    assert "- 核心仓库目录：`core/`" in memory
    assert "- 项目根目录：`projects/`" in memory
    assert "- 持久状态记录目录：`docs/memory/`" in memory
    assert "- 技能沉淀目录：`docs/skills/`" in memory


def test_setup_workspace_english_language_creates_english_templates(tmp_path: Path):
    workspace_dir = tmp_path / "workspace"

    result = _run_chattool_setup_workspace(
        [str(workspace_dir), "--language", "en", "-I"]
    )

    assert result.returncode == 0, result.stderr
    readme = (workspace_dir / "README.md").read_text(encoding="utf-8")
    agents = (workspace_dir / "AGENTS.md").read_text(encoding="utf-8")
    memory = (workspace_dir / "MEMORY.md").read_text(encoding="utf-8")
    assert "## Architecture" in agents
    assert "## 架构" not in agents
    assert "## Current Workspace" in memory
    assert "Human-AI collaboration workspace root." in readme


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

    projects_readme = workspace_dir / "projects" / "README.md"
    projects_readme.write_text("custom projects readme\n", encoding="utf-8")

    second = _run_chattool_setup_workspace([str(workspace_dir), "--force", "-I"])
    assert second.returncode == 0, second.stderr
    assert projects_readme.read_text(encoding="utf-8") != "custom projects readme\n"


def test_setup_workspace_existing_workspace_keeps_protocol_files(tmp_path: Path):
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
    assert not (workspace_dir / "AGENTS.generated.md").exists()
    assert not (workspace_dir / "MEMORY.generated.md").exists()
    assert (workspace_dir / "README.md").exists()
