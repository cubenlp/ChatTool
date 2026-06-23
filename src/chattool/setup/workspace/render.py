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


def render_archive_index(language: str) -> str:
    if language == "en":
        return (
            "# Archived Content Index\n\n"
            "This file records what has already been archived in `archive/`. Keep entries in reverse chronological order.\n\n"
            "## Structure\n\n"
            "```text\narchive/\n  index.md\n  YYYY-MM-DD/\n    <project-name>/\n```\n\n"
            "## Entries\n\n"
            "- No archived projects recorded yet.\n"
        )
    return (
        "# 已归档内容索引\n\n"
        "这里记录 `archive/` 里已经有哪些归档项目，按归档日期倒序维护。\n\n"
        "## 目录结构\n\n"
        "```text\narchive/\n  index.md\n  YYYY-MM-DD/\n    <project-name>/\n```\n\n"
        "## 条目\n\n"
        "- 暂无已记录的归档项目。\n"
    )


def render_archive_md(language: str) -> str:
    if language == "en":
        return (
            "# Archive Guide\n\n"
            "This guide explains how to archive inactive workspace projects.\n\n"
            "## Flow\n\n"
            "1. Collect candidate projects with scripts or directory review.\n"
            "2. Let the model review candidates before moving anything.\n"
            "3. Move inactive projects to `archive/YYYY-MM-DD/<project-name>/`; do not delete content.\n"
            "4. Update `archive/index.md` with a concise summary of what was archived and why.\n"
        )
    return (
        "# 归档操作指南\n\n"
        "这里说明如何归档不再活跃的 workspace project。\n\n"
        "## 流程\n\n"
        "1. 先用脚本或目录审查收集候选 project。\n"
        "2. 由模型审查候选，不要纯脚本盲搬。\n"
        "3. 将不活跃 project 移到 `archive/YYYY-MM-DD/<project-name>/`，不要删除内容。\n"
        "4. 在 `archive/index.md` 记录本次已归档内容和简要原因。\n"
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
        "- use root `ARCHIVE.md` as the archive procedure guide, and update `archive/index.md` when projects are archived or restored\n"
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
        "- 根 `ARCHIVE.md` 作为归档操作指南；发生归档或恢复时同步更新 `archive/index.md`\n"
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
        "archive/index.md": render_archive_index(language),
        "scripts/README.md": render_scripts_readme(language),
        "public/README.md": render_public_readme(language),
    }
    skill_md, skill_zh = render_workspace_maintenance_skill()
    file_map["skills/local/workspace-maintenance/SKILL.md"] = skill_md
    file_map["skills/local/workspace-maintenance/SKILL.zh.md"] = skill_zh
    agents_content = render_agents_md(workspace_dir, profile, language, enabled_options)
    if helper_agents_path:
        file_map[helper_agents_path] = agents_content
    else:
        file_map["AGENTS.md"] = agents_content
    file_map.update(profile.extra_files(workspace_dir))
    return file_map
