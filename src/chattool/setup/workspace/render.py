from __future__ import annotations

from importlib import resources
from pathlib import Path

from .core import WorkspaceProfile


def _read_template(language: str, relative_path: str) -> str:
    return (
        resources.files("chattool.setup.workspace")
        .joinpath("templates")
        .joinpath(language)
        .joinpath(relative_path)
        .read_text(encoding="utf-8")
    )


def _render_text_template(language: str, relative_path: str, **variables: str) -> str:
    content = _read_template(language, relative_path)
    for key, value in variables.items():
        content = content.replace(f"{{{{{key}}}}}", value)
    return content


def render_root_readme(language: str) -> str:
    return _read_template(language, "README.md")


def render_projects_readme(language: str) -> str:
    return _read_template(language, "projects/README.md")


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


def render_public_readme(language: str) -> str:
    if language == "en":
        return "# Public\n\nThis directory is used for deploying public-facing websites and related publish artifacts.\n"
    return "# Public\n\n这个目录用于部署公开网站及相关发布产物。\n"


def render_memory_md(language: str) -> str:
    return _read_template(language, "MEMORY.md")


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
    helper_memory_path: str | None = None,
) -> dict[str, str]:
    file_map = {
        "README.md": render_root_readme(language),
        "TODO.md": "# TODO\n\n",
        "projects/README.md": render_projects_readme(language),
        "docs/README.md": render_docs_readme(language),
        "docs/memory/README.md": render_docs_memory_readme(language),
        "docs/skills/README.md": render_docs_skills_readme(language),
        "docs/tools/README.md": render_docs_tools_readme(language),
        "public/README.md": render_public_readme(language),
    }
    agents_content = render_agents_md(workspace_dir, profile, language, enabled_options)
    memory_content = render_memory_md(language)
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
