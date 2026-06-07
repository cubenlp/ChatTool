from __future__ import annotations

from importlib import resources
from pathlib import Path

from .core import WorkspaceProfile


def _read_template(language: str, relative_path: str) -> str:
    return (
        resources.files("chattool.setup.workspace")
        .joinpath("templates")
        .joinpath("default")
        .joinpath(language)
        .joinpath(relative_path)
        .read_text(encoding="utf-8")
    )


def _render_text_template(language: str, relative_path: str, **variables: str) -> str:
    content = _read_template(language, relative_path)
    for key, value in variables.items():
        content = content.replace(f"{{{{{key}}}}}", value)
    return content


def render_projects_readme(language: str) -> str:
    return _read_template(language, "projects/README.md")


def render_archive_readme(language: str) -> str:
    if language == "en":
        return (
            "# Archive README\n\n"
            "`archive/` stores inactive projects by archive date.\n\n"
            "## Structure\n\n"
            "```text\narchive/\n  README.md\n  YYYY-MM-DD/\n    <project-name>/\n```\n\n"
            "Move inactive projects into `archive/YYYY-MM-DD/` and summarize them in the workspace root `ARCHIVE.md`.\n"
        )
    return (
        "# Archive README\n\n"
        "`archive/` 是 Playground 的历史日志区，按归档日期保存已不活跃的 project。\n\n"
        "## 目录结构\n\n"
        "```text\narchive/\n  README.md\n  YYYY-MM-DD/\n    <project-name>/\n```\n\n"
        "每次归档时，把 project 移到 `archive/YYYY-MM-DD/`，并在 workspace 根目录 `ARCHIVE.md` 中补归档摘要。\n"
    )


def render_archive_md(language: str) -> str:
    if language == "en":
        return "# Archive\n\nRecord archived project summaries in reverse chronological order.\n"
    return (
        "# Archive\n\n"
        "按日期倒序记录归档项目摘要。每个项目都说明“这是做什么的”和“本轮做了什么”。更具体的维护规则见 `archive/README.md`。\n"
    )


def render_todo_md(language: str) -> str:
    if language == "en":
        return "# TODO\n\nNear-term plans for this workspace.\n"
    return "# TODO\n\n这里记录这个 workspace 近期打算做的事。\n"


def render_scripts_readme(language: str) -> str:
    if language == "en":
        return (
            "# Scripts\n\n"
            "Workspace-level maintenance scripts live here. Keep task-specific scripts inside the relevant project.\n"
        )
    return (
        "# Scripts\n\n"
        "这里放 workspace 级维护脚本。\n\n"
        "约定：\n"
        "- 只放跨 project 复用的维护脚本\n"
        "- 不要在 workspace 顶层散放脚本或临时文件\n"
        "- 业务任务相关脚本，优先放在对应 project 内部\n"
    )


def render_workspace_maintenance_skill() -> tuple[str, str]:
    skill_md = (
        "---\n"
        "name: workspace-maintenance\n"
        "description: Maintain the outer workspace structure. Use for project cleanup, archive review, root protocol alignment, and moving files into the proper workspace-level locations.\n"
        "version: 0.2.2\n"
        "---\n\n"
        "# Workspace Maintenance\n\n"
        "Use this skill when maintaining the outer workspace rather than editing a source repository.\n\n"
        "- keep active work under `projects/` and archive inactive work into `archive/YYYY-MM-DD/`\n"
        "- update `ARCHIVE.md` when projects are archived or restored\n"
        "- keep workspace-level scripts under `scripts/`\n"
        "- prefer moving files into the nearest `.trash/` instead of deleting them directly\n"
        "- keep root protocol files (`AGENTS.md`, `ARCHIVE.md`, `TODO.md`) aligned with the real workspace structure\n"
    )
    skill_zh = (
        "---\n"
        "name: workspace-maintenance\n"
        "description: 维护 workspace 外层协作结构。适用于整理活跃项目、归档旧项目、对齐根协议文件，以及把文件移动到正确的 workspace 级目录。\n"
        "version: 0.2.2\n"
        "---\n\n"
        "# Workspace Maintenance（中文）\n\n"
        "用于维护 workspace 外层结构，而不是直接修改源码仓库。\n\n"
        "- 活跃工作保留在 `projects/`，不活跃项目归档到 `archive/YYYY-MM-DD/`\n"
        "- 发生归档或恢复时同步更新 `ARCHIVE.md`\n"
        "- workspace 级维护脚本统一放到 `scripts/`\n"
        "- 删除前优先移动到就近的 `.trash/`，不要直接删除\n"
        "- 保持根协议文件（`AGENTS.md`、`ARCHIVE.md`、`TODO.md`）与真实结构一致\n"
    )
    return skill_md, skill_zh


def render_public_readme(language: str) -> str:
    if language == "en":
        return "# Public\n\nThis directory is used for deploying public-facing websites and related publish artifacts.\n"
    return "# Public\n\n这个目录用于部署公开网站及相关发布产物。\n"


def render_agents_md(
    workspace_dir: Path,
    profile: WorkspaceProfile,
    language: str,
    enabled_options: list[str],
) -> str:
    options_text = ", ".join(enabled_options) if enabled_options else "none"
    return _render_text_template(language, "AGENTS.md", ENABLED_OPTIONS=options_text)


def base_file_map(
    workspace_dir: Path,
    profile: WorkspaceProfile,
    language: str,
    enabled_options: list[str],
    *,
    existing_workspace: bool,
    helper_agents_path: str | None = None,
    helper_identity_path: str | None = None,
) -> dict[str, str]:
    file_map = {
        "TODO.md": render_todo_md(language),
        "ARCHIVE.md": render_archive_md(language),
        "projects/README.md": render_projects_readme(language),
        "archive/README.md": render_archive_readme(language),
        "scripts/README.md": render_scripts_readme(language),
        "public/README.md": render_public_readme(language),
    }
    skill_md, skill_zh = render_workspace_maintenance_skill()
    file_map["skills/workspace-maintenance/SKILL.md"] = skill_md
    file_map["skills/workspace-maintenance/SKILL.zh.md"] = skill_zh
    agents_content = render_agents_md(workspace_dir, profile, language, enabled_options)
    if helper_agents_path:
        file_map[helper_agents_path] = agents_content
    else:
        file_map["AGENTS.md"] = agents_content
    file_map.update(profile.extra_files(workspace_dir))
    return file_map
