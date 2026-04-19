from __future__ import annotations

from importlib import resources
from pathlib import Path

from .core import WorkspaceProfile


def _read_template(language: str, relative_path: str, *, template_variant: str = "default") -> str:
    return (
        resources.files("chattool.setup.workspace")
        .joinpath("templates")
        .joinpath(template_variant)
        .joinpath(language)
        .joinpath(relative_path)
        .read_text(encoding="utf-8")
    )


def _render_text_template(language: str, relative_path: str, *, template_variant: str = "default", **variables: str) -> str:
    content = _read_template(language, relative_path, template_variant=template_variant)
    for key, value in variables.items():
        content = content.replace(f"{{{{{key}}}}}", value)
    return content


def render_root_readme(language: str, *, template_variant: str = "default") -> str:
    return _read_template(language, "README.md", template_variant=template_variant)


def render_projects_readme(language: str, *, template_variant: str = "default") -> str:
    return _read_template(language, "projects/README.md", template_variant=template_variant)


def render_docs_readme(language: str) -> str:
    if language == "en":
        return "# Docs\n\nDurable notes outside source repositories.\n"
    return "# Docs\n\n源码仓库之外的长期文档区。\n"


def render_docs_memory_readme(language: str) -> str:
    if language == "en":
        return "# Memory\n\nDurable status snapshots and long-lived context.\n"
    return "# Memory\n\n状态快照与长期上下文。\n"


def render_docs_tools_readme(language: str) -> str:
    if language == "en":
        return "# Tools\n\nTool-specific notes and references.\n"
    return "# Tools\n\n工具说明与参考。\n"


def render_docs_skills_readme(language: str) -> str:
    if language == "en":
        return "# Skills\n\nReusable skills, patterns, and practice notes.\n"
    return "# Skills\n\n可复用技巧、skills 与实践记录。\n"


def render_reference_readme(language: str) -> str:
    if language == "en":
        return "# Reference\n\nReusable workspace-level references shared across multiple projects.\n"
    return "# Reference\n\n跨多个 project 可复用的 workspace 级长期参考。\n"


def render_docs_themes_readme(language: str) -> str:
    if language == "en":
        return "# Themes\n\nLong-lived workspace conventions organized by theme.\n"
    return "# Themes\n\n按主题整理的 workspace 长期规范与维护约定。\n"


def render_docs_theme_changelog(language: str) -> str:
    if language == "en":
        return (
            "# Changelog Theme\n\n"
            "Current workspace changelog rules:\n\n"
            "- Maintain `CHANGELOG.md` entries with explicit dates\n"
            "- Do not introduce a parallel `release.log` mechanism unless a repo already has one\n"
            "- Use project `progress.md` for task process notes, not repo changelogs\n"
        )
    return (
        "# Changelog Theme\n\n"
        "当前 workspace 的 changelog 维护约定：\n\n"
        "- `CHANGELOG.md` 按日期维护条目\n"
        "- 不额外引入 `release.log` 这一类平行机制，除非某个仓库自己已经有明确入口\n"
        "- project 的 `progress.md` 用来记录任务推进过程，不替代仓库 changelog\n"
    )


def render_workspace_maintenance_skill(language: str) -> tuple[str, str]:
    skill_md = (
        "---\n"
        "name: workspace-maintenance\n"
        "description: Maintain the outer workspace structure. Use when organizing projects, promoting reusable materials into workspace-level reference, or normalizing long-lived rules into docs/themes.\n"
        "version: 0.1.0\n"
        "---\n\n"
        "# Workspace Maintenance\n\n"
        "Use this skill for outer-workspace cleanup and normalization.\n\n"
        "- promote reusable materials into `reference/`\n"
        "- normalize long-lived rules into `docs/themes/`\n"
        "- keep project-local `reference/` directories task-specific\n"
        "- update root docs when workspace structure changes\n"
    )
    skill_zh = (
        "---\n"
        "name: workspace-maintenance\n"
        "description: 维护 workspace 外层协作结构。适用于整理 projects、把可复用材料提升到 workspace 级 reference、把长期规范收口到 docs/themes。\n"
        "version: 0.1.0\n"
        "---\n\n"
        "# Workspace Maintenance（中文）\n\n"
        "用于 workspace 外层整理与规范化。\n\n"
        "- 把可复用材料沉淀到 `reference/`\n"
        "- 把长期规则收口到 `docs/themes/`\n"
        "- 保持 project 内 `reference/` 只服务当前任务\n"
        "- workspace 结构变化后同步更新根文档\n"
    )
    return (skill_md, skill_zh) if language == "en" else (skill_zh, skill_zh)


def render_public_readme(language: str) -> str:
    if language == "en":
        return "# Public\n\nThis directory is used for deploying public-facing websites and related publish artifacts.\n"
    return "# Public\n\n这个目录用于部署公开网站及相关发布产物。\n"


def render_memory_md(language: str, *, template_variant: str = "default") -> str:
    return _read_template(language, "MEMORY.md", template_variant=template_variant)


def render_agents_md(
    workspace_dir: Path,
    profile: WorkspaceProfile,
    language: str,
    enabled_options: list[str],
    *,
    template_variant: str = "default",
) -> str:
    options_text = ", ".join(enabled_options) if enabled_options else "none"
    return _render_text_template(language, "AGENTS.md", template_variant=template_variant, ENABLED_OPTIONS=options_text)


def base_file_map(
    workspace_dir: Path,
    profile: WorkspaceProfile,
    language: str,
    enabled_options: list[str],
    *,
    template_variant: str = "default",
    existing_workspace: bool,
    helper_agents_path: str | None = None,
    helper_memory_path: str | None = None,
) -> dict[str, str]:
    file_map = {
        "README.md": render_root_readme(language, template_variant=template_variant),
        "TODO.md": "# TODO\n\n",
        "projects/README.md": render_projects_readme(language, template_variant=template_variant),
        "reference/README.md": render_reference_readme(language),
        "docs/README.md": render_docs_readme(language),
        "docs/memory/README.md": render_docs_memory_readme(language),
        "docs/skills/README.md": render_docs_skills_readme(language),
        "docs/themes/README.md": render_docs_themes_readme(language),
        "docs/themes/changelog.md": render_docs_theme_changelog(language),
        "docs/tools/README.md": render_docs_tools_readme(language),
        "public/README.md": render_public_readme(language),
    }
    skill_md, skill_zh = render_workspace_maintenance_skill(language)
    file_map["skills/workspace-maintenance/SKILL.md"] = skill_md
    file_map["skills/workspace-maintenance/SKILL.zh.md"] = skill_zh
    agents_content = render_agents_md(workspace_dir, profile, language, enabled_options, template_variant=template_variant)
    memory_content = render_memory_md(language, template_variant=template_variant)
    if helper_agents_path:
        file_map[helper_agents_path] = agents_content
    else:
        file_map["AGENTS.md"] = agents_content
    if helper_memory_path:
        file_map[helper_memory_path] = memory_content
    else:
        file_map["MEMORY.md"] = memory_content
    file_map.update(profile.extra_files(workspace_dir))
    return file_map
