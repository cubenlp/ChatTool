from __future__ import annotations

from pathlib import Path

from .core import WorkspaceProfile


def render_root_readme(language: str) -> str:
    if language == "en":
        return "# Workspace\n\nHuman-AI collaboration workspace root.\n"
    return "# Workspace\n\n人类-AI 协作 workspace 根目录。\n"


def render_reports_readme(language: str) -> str:
    if language == "en":
        return "# Reports\n\nHuman-facing task reports.\n"
    return "# Reports\n\n面向人的任务汇报区。\n"


def render_playgrounds_readme(language: str) -> str:
    if language == "en":
        return "# Playgrounds\n\nTask-isolated work area for drafts and experiments.\n"
    return "# Playgrounds\n\n任务隔离的草稿、实验和中间工作区。\n"


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


def render_public_readme(language: str) -> str:
    if language == "en":
        return "# Public\n\nThis directory is used for deploying public-facing websites and related publish artifacts.\n"
    return "# Public\n\n这个目录用于部署公开网站及相关发布产物。\n"


def render_memory_md(language: str) -> str:
    if language == "en":
        return (
            "# Workspace Memory\n\n"
            "## Current Workspace\n\n"
            "- Reports root: `reports/`\n"
            "- Task playgrounds root: `playgrounds/`\n"
            "- Core repositories root: `core/`\n"
            "- Shared skills root: `skills/`\n"
            "- Public publish root: `public/`\n"
            "- Reference materials root: `reference/`\n"
        )
    return (
        "# Workspace Memory\n\n"
        "## 当前 Workspace\n\n"
        "- 汇报根目录：`reports/`\n"
        "- 任务工作区根目录：`playgrounds/`\n"
        "- 核心仓库目录：`core/`\n"
        "- 共享 skills 目录：`skills/`\n"
        "- 对外发布目录：`public/`\n"
        "- 参考资料目录：`reference/`\n"
    )


def render_agents_md(
    workspace_dir: Path,
    profile: WorkspaceProfile,
    language: str,
    enabled_options: list[str],
) -> str:
    options_text = ", ".join(enabled_options) if enabled_options else "none"
    if language == "en":
        return (
            "# Workspace Agents\n\n"
            "This workspace is organized around reports, playgrounds, core repos, shared skills, and public output.\n\n"
            "## Current Options\n\n"
            f"- Enabled options: `{options_text}`\n"
            "- Core repos go under `core/`\n"
            "- Shared skills go under `skills/`\n"
            "- Public site output goes under `public/`\n"
        )
    return (
        "# Workspace Agents\n\n"
        "这个 workspace 以 reports、playgrounds、core 仓库、共享 skills 和 public 输出目录组织。\n\n"
        "## 当前配置项\n\n"
        f"- 已启用项：`{options_text}`\n"
        "- 核心仓库放到 `core/`\n"
        "- 共享 skills 放到 `skills/`\n"
        "- 对外发布站点输出放到 `public/`\n"
    )


def base_file_map(
    workspace_dir: Path,
    profile: WorkspaceProfile,
    language: str,
    enabled_options: list[str],
) -> dict[str, str]:
    file_map = {
        "README.md": render_root_readme(language),
        "AGENTS.md": render_agents_md(
            workspace_dir, profile, language, enabled_options
        ),
        "MEMORY.md": render_memory_md(language),
        "TODO.md": "# TODO\n\n",
        "reports/README.md": render_reports_readme(language),
        "playgrounds/README.md": render_playgrounds_readme(language),
        "docs/README.md": render_docs_readme(language),
        "docs/memory/README.md": render_docs_memory_readme(language),
        "docs/tools/README.md": render_docs_tools_readme(language),
        "public/README.md": render_public_readme(language),
    }
    file_map.update(profile.extra_files(workspace_dir))
    return file_map
