from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import click

from chattool.setup.common import display_path, resolve_workspace_dir, write_text_file
from chattool.setup.interactive import (
    abort_if_force_without_tty,
    resolve_interactive_mode,
)
from chattool.setup.playground import (
    _copy_skills,
    _default_chattool_source,
    _ensure_chattool_repo,
    _maybe_setup_github_auth,
    _should_sync_skills,
    _validate_cloned_repo,
    _workspace_skills_source,
)
from chattool.utils.custom_logger import setup_logger
from chattool.utils.tui import BACK_VALUE, ask_select, ask_text, create_choice

logger = setup_logger("setup_workspace")

DEFAULT_LANGUAGE = "zh"
SUPPORTED_LANGUAGES = {"zh", "en"}


@dataclass(frozen=True)
class WorkspaceProfile:
    name: str
    description: str

    def extra_dirs(self) -> list[str]:
        return []

    def extra_files(self, workspace: Path, **ctx) -> dict[str, str]:
        return {}

    def agents_md_appendix(self, **ctx) -> str:
        return ""


class BaseProfile(WorkspaceProfile):
    pass


PROFILES: dict[str, WorkspaceProfile] = {
    "base": BaseProfile(
        name="base", description="General-purpose human-AI collaboration workspace."
    ),
}

BASE_DIRS = [
    "reports",
    "playgrounds",
    "docs",
    "docs/memory",
    "docs/skills",
    "docs/tools",
    "core",
    "reference",
]


def _resolve_profile(profile_name: str | None) -> WorkspaceProfile:
    key = (profile_name or "base").strip().lower()
    profile = PROFILES.get(key)
    if profile is None:
        supported = ", ".join(sorted(PROFILES))
        raise click.ClickException(
            f"Unknown workspace profile: {profile_name}. Supported: {supported}"
        )
    return profile


def _coerce_profile_and_workspace(
    profile_name, workspace_dir
) -> tuple[str | None, str | None]:
    if profile_name and workspace_dir is None:
        candidate = str(profile_name).strip()
        if candidate.lower() not in PROFILES:
            return None, candidate
    return profile_name, workspace_dir


def _resolve_language(language: str | None) -> str:
    key = (language or DEFAULT_LANGUAGE).strip().lower()
    if key not in SUPPORTED_LANGUAGES:
        supported = ", ".join(sorted(SUPPORTED_LANGUAGES))
        raise click.ClickException(
            f"Unknown workspace language: {language}. Supported: {supported}"
        )
    return key


def _render_chattool_md(language: str) -> str:
    if language == "en":
        return (
            "# ChatTool Workspace Guide\n\n"
            "This workspace can optionally place a `ChatTool/` repository at the root as a reusable capability source.\n\n"
            "## Purpose\n\n"
            "- Keep the workspace structure stable even when ChatTool is absent.\n"
            "- When ChatTool is present, treat it as a source repository to update under the workspace root.\n"
            "- Sync reusable skills from `ChatTool/skills/` into `docs/skills/` while keeping local `experience/` notes untouched.\n\n"
            "## Suggestions\n\n"
            "- Put implementation changes into `ChatTool/` when they belong to ChatTool itself.\n"
            "- Put reusable usage notes and practice logs into `docs/skills/`.\n"
            "- Keep temporary experiments in task-specific playgrounds instead of the repo root.\n"
        )
    return (
        "# ChatTool Workspace 指南\n\n"
        "这个 workspace 可以选择在根目录放一个 `ChatTool/` 仓库，作为可复用能力来源。\n\n"
        "## 目的\n\n"
        "- 即使不添加 ChatTool，workspace 结构也保持稳定。\n"
        "- 添加 ChatTool 后，把它视为放在 workspace 根目录下的待更新源码仓库。\n"
        "- 把 `ChatTool/skills/` 中可复用的 skills 同步到 `docs/skills/`，同时保留本地 `experience/` 记录。\n\n"
        "## 建议\n\n"
        "- 属于 ChatTool 本身的实现改动尽量写进 `ChatTool/`。\n"
        "- 可复用的使用说明和练习记录写进 `docs/skills/`。\n"
        "- 临时实验尽量放在任务 playground，不要堆在仓库根目录。\n"
    )


def _render_agents_md(
    workspace_dir: Path,
    profile: WorkspaceProfile,
    language: str,
    with_chattool: bool,
) -> str:
    appendix = profile.agents_md_appendix(workspace=workspace_dir)
    if language == "en":
        chattool_lines = (
            "- `ChatTool/`: optional source repository stored at workspace root.\n"
            if with_chattool
            else ""
        )
        return (
            "# Workspace Agents\n\n"
            "`AGENTS.md` is the entry point for models working in this workspace.\n\n"
            "## Core Principles\n\n"
            "- Keep human-facing progress and results in `reports/`; do not mix drafts, experiments, or intermediate files into it.\n"
            "- Work is divided into two types: `task` and `taskset`.\n"
            "- Default to `task`; only use `taskset` when the work is clearly a long-running series around one larger goal.\n"
            "- When multiple tasks run in parallel, both `reports/` and `playgrounds/` must stay task-isolated.\n\n"
            "### task\n\n"
            "- A `task` corresponds to one standalone objective.\n"
            "- Report under `reports/MM-DD-<task-name>/`.\n"
            "- Work under `playgrounds/<task-name>/`.\n"
            "- Each task directory should at least contain `TASK.md`, `progress.md`, and `SUMMARY.md`.\n\n"
            "### taskset\n\n"
            "- A `taskset` corresponds to a series of tasks advancing one larger goal.\n"
            "- Use `reports/MM-DD-<set-name>/` for the task-set report root.\n"
            "- Use `playgrounds/task-sets/<set-name>/` for the shared work root.\n"
            "- A task set may keep a shared `progress.md` so follow-up tasks can continue directly.\n"
            "- A task set may continue to split into per-task subdirectories when needed.\n\n"
            "## Architecture\n\n"
            "```text\n"
            "Workspace/\n"
            "  MEMORY.md\n"
            "  TODO.md\n"
            "  reports/\n"
            "  playgrounds/\n"
            "  docs/\n"
            "  core/\n"
            "  reference/\n"
            "```\n\n"
            "This workspace sits around the source repositories being changed. Collaboration traces stay in the outer workspace so core projects remain clean.\n\n"
            "### Key File Roles\n\n"
            "- `MEMORY.md`: cross-session state. Read it every session before substantive work.\n"
            "- `TODO.md`: lightweight human draft pad for rough notes, ideas, and pending items.\n"
            "- `reports/`: human-facing reporting area.\n"
            "- `playgrounds/`: task-isolated work roots for drafts, experiments, and intermediate files.\n"
            "- `docs/`: concise durable notes outside source repositories. Use `docs/memory/`, `docs/skills/`, and `docs/tools/`.\n"
            "- `core/`: source repositories that need implementation or updates.\n"
            "- `reference/`: research material, external docs, samples, and other read-only references.\n"
            f"{chattool_lines}"
            "\n"
            "### Task Directories\n\n"
            "```text\n"
            "reports/\n"
            "  MM-DD-<task-name>/\n"
            "  MM-DD-<set-name>/\n"
            "\n"
            "playgrounds/\n"
            "  <task-name>/\n"
            "  task-sets/<set-name>/\n"
            "```\n\n"
            "- A regular task uses `reports/MM-DD-<task-name>/` and `playgrounds/<task-name>/`.\n"
            "- A task-set task uses `reports/MM-DD-<set-name>/` and `playgrounds/task-sets/<set-name>/`.\n"
            "- When tasks run in parallel, each task keeps its own isolated report and playground.\n\n"
            "### Docs Directories\n\n"
            "```text\n"
            "docs/\n"
            "  memory/\n"
            "  skills/\n"
            "  tools/\n"
            "```\n\n"
            "- `docs/memory/`: durable status notes and key context.\n"
            "- `docs/skills/`: reusable techniques, copied skills, and practice logs.\n"
            "- `docs/tools/`: tool-specific usage discoveries and pitfalls.\n\n"
            "### Reports Structure\n\n"
            "```text\n"
            "reports/MM-DD-<task-name>/\n"
            "  TASK.md\n"
            "  progress.md\n"
            "  SUMMARY.md\n"
            "\n"
            "reports/MM-DD-<set-name>/\n"
            "  TASKSET.md\n"
            "  progress.md\n"
            "  <1-task-name>/\n"
            "    TASK.md\n"
            "    progress.md\n"
            "    SUMMARY.md\n"
            "```\n\n"
            "## Workflow\n\n"
            "1. Read `MEMORY.md` to load cross-session context and active constraints.\n"
            "2. Identify the source repositories involved. Put repositories to modify under `core/`, and put research materials under `reference/`.\n"
            "3. Default to `task`; only switch to `taskset` when the work is clearly a task series around one goal.\n"
            "4. For a regular task, work inside `playgrounds/<task-name>/` and report in `reports/MM-DD-<task-name>/`.\n"
            "5. For a task set, work inside `playgrounds/task-sets/<set-name>/` and report under `reports/MM-DD-<set-name>/<task-name>/`.\n"
            "6. While executing a task, stay focused on that task only.\n"
            "7. During wrap-up, finish the current task report first; if it belongs to a task set, then update the task-set `progress.md` and prepare the next task.\n"
            "8. Write durable findings into `docs/` so they stay outside source repositories.\n"
            "9. Update `MEMORY.md` before ending the session so key context survives.\n\n"
            "## Write Rules\n\n"
            "| Situation | Write to |\n"
            "|-----------|----------|\n"
            "| Draft / experiment / temporary work note | `playgrounds/<task-name>/` |\n"
            "| Human-facing task report | `reports/MM-DD-<task-name>/` |\n"
            "| Human-facing task-set overview | `reports/MM-DD-<set-name>/TASKSET.md` and `reports/MM-DD-<set-name>/progress.md` |\n"
            "| Source repository to modify | `core/<repo-name>/` |\n"
            "| Research material / external references / samples | `reference/<topic-or-source>/` |\n"
            "| Status snapshot / durable context | `docs/memory/YYYY-MM-DD-status.md` |\n"
            "| Tool usage discovery | `docs/tools/<toolname>.md` |\n"
            "| Reusable technique / skill note | `docs/skills/` |\n\n"
            "## Conventions\n\n"
            "- `reports/` only carries human-facing goals, progress, summaries, and task-set overviews.\n"
            "- `docs/` is concise; keep only durable notes there.\n"
            "- `core/` only contains repositories to update, not reports or notes.\n"
            "- `reference/` only contains reference material, not the main repository to modify.\n"
            f"{appendix}"
        )

    chattool_lines = (
        "- `ChatTool/`：可选的源码仓库，直接放在 workspace 根目录。\n"
        if with_chattool
        else ""
    )
    return (
        "# Workspace Agents\n\n"
        "`AGENTS.md` 是模型进入这个 workspace 后的入口说明。\n\n"
        "## 核心原则\n\n"
        "- 汇报统一放在 `reports/`，不要把草稿、实验和中间材料混进来。\n"
        "- 任务分为两类：`task` 和 `taskset`。\n"
        "- 默认使用 `task`；只有明确是一组围绕同一目标持续推进的任务，才使用 `taskset`。\n"
        "- 多个任务并行时，`reports/` 和 `playgrounds/` 都必须按任务隔离，避免互相污染。\n\n"
        "### task\n\n"
        "- 对应一次独立目标。\n"
        "- 报告目录使用 `reports/MM-DD-<task-name>/`。\n"
        "- 工作目录使用 `playgrounds/<task-name>/`。\n"
        "- 每个任务目录至少包含 `TASK.md`、`progress.md` 和 `SUMMARY.md`。\n\n"
        "### taskset\n\n"
        "- 对应围绕同一大目标持续推进的一组任务。\n"
        "- 任务集目录使用 `reports/MM-DD-<set-name>/`。\n"
        "- 工作根目录使用 `playgrounds/task-sets/<set-name>/`。\n"
        "- 任务集可以维护一个共享 `progress.md`，让后续任务直接承接。\n"
        "- 任务集内部可以继续拆分子任务目录。\n\n"
        "## 架构\n\n"
        "```text\n"
        "Workspace/\n"
        "  MEMORY.md\n"
        "  TODO.md\n"
        "  reports/\n"
        "  playgrounds/\n"
        "  docs/\n"
        "  core/\n"
        "  reference/\n"
        "```\n\n"
        "这个 workspace 是包裹源码仓库的一层协作脚手架。协作痕迹尽量都留在外层 workspace，核心项目保持干净。\n\n"
        "### 关键文件职责\n\n"
        "- `MEMORY.md`：跨 session 记忆。每次进入工作前都先读。\n"
        "- `TODO.md`：给人的轻量草稿区，用于随手记想法、待办和未整理条目。\n"
        "- `reports/`：面向人的汇报区。\n"
        "- `playgrounds/`：模型的工作区根目录。草稿、实验和中间文件都放在这里。\n"
        "- `docs/`：更简洁的长期文档区。使用 `docs/memory/`、`docs/skills/`、`docs/tools/`。\n"
        "- `core/`：集中存放需要更新、实现或修复的源码仓库。\n"
        "- `reference/`：集中存放调研资料、外部文档摘录、竞品样例、数据样本和其他只读参考材料。\n"
        f"{chattool_lines}"
        "\n"
        "### 任务目录\n\n"
        "```text\n"
        "reports/\n"
        "  MM-DD-<task-name>/\n"
        "  MM-DD-<set-name>/\n"
        "\n"
        "playgrounds/\n"
        "  <task-name>/\n"
        "  task-sets/<set-name>/\n"
        "```\n\n"
        "- 常规任务：对应一次独立目标，使用 `reports/MM-DD-<task-name>/` 和 `playgrounds/<task-name>/`。\n"
        "- 任务集任务：对应围绕同一大目标持续推进的一组任务，使用 `reports/MM-DD-<set-name>/` 和 `playgrounds/task-sets/<set-name>/`。\n"
        "- 多任务并行时，每个任务都要有自己独立的 report 和 playground，避免相互污染。\n\n"
        "### Docs 目录\n\n"
        "```text\n"
        "docs/\n"
        "  memory/\n"
        "  skills/\n"
        "  tools/\n"
        "```\n\n"
        "- `docs/memory/`：状态快照、长期上下文和关键说明。\n"
        "- `docs/skills/`：可复用技巧、同步出来的 skills 和 practice 记录。\n"
        "- `docs/tools/`：围绕某个工具的使用发现、踩坑和经验。\n\n"
        "### Reports 结构\n\n"
        "```text\n"
        "reports/MM-DD-<task-name>/\n"
        "  TASK.md\n"
        "  progress.md\n"
        "  SUMMARY.md\n"
        "\n"
        "reports/MM-DD-<set-name>/\n"
        "  TASKSET.md\n"
        "  progress.md\n"
        "  <1-task-name>/\n"
        "    TASK.md\n"
        "    progress.md\n"
        "    SUMMARY.md\n"
        "```\n\n"
        "## 工作流\n\n"
        "1. 先读 `MEMORY.md`，加载跨 session 的背景、约束和当前上下文。\n"
        "2. 识别当前涉及的源码仓库，把待修改项目放在 `core/`，把参考资料放在 `reference/`。\n"
        "3. 默认先判断为 `task`；只有明确是一串围绕同一目标推进的任务，才切换到 `taskset`。\n"
        "4. 常规任务在 `playgrounds/<task-name>/` 下工作，并在 `reports/MM-DD-<task-name>/` 下汇报。\n"
        "5. 任务集任务在 `playgrounds/task-sets/<set-name>/` 下工作，并在 `reports/MM-DD-<set-name>/<task-name>/` 下汇报。\n"
        "6. 任务执行过程中，只专注当前任务本身。\n"
        "7. 每次收尾时，先完成当前任务的汇报；如果该任务属于任务集，再更新任务集级 `progress.md`，并衔接下一个任务。\n"
        "8. 把可复用结论写入 `docs/`，让长期文档留在项目外层。\n"
        "9. 结束前更新 `MEMORY.md`，保留下一次继续工作的必要上下文。\n\n"
        "## 写入规则\n\n"
        "| 情况 | 写入位置 |\n"
        "|-----------|----------|\n"
        "| 草稿 / 实验 / 临时工作文档 | `playgrounds/<task-name>/` |\n"
        "| 给人的任务汇报 | `reports/MM-DD-<task-name>/` |\n"
        "| 给人的任务集总览 | `reports/MM-DD-<set-name>/TASKSET.md` 和 `reports/MM-DD-<set-name>/progress.md` |\n"
        "| 需要修改的源码仓库 | `core/<repo-name>/` |\n"
        "| 调研资料 / 外部参考 / 样例 | `reference/<topic-or-source>/` |\n"
        "| 状态快照 / 长期上下文 | `docs/memory/YYYY-MM-DD-status.md` |\n"
        "| 工具使用发现 | `docs/tools/<toolname>.md` |\n"
        "| 可复用技巧 / skill 说明 | `docs/skills/` |\n\n"
        "## 约定\n\n"
        "- `reports/` 只承载面向人的目标、阶段进展、最终总结，以及任务集总览。\n"
        "- `docs/` 保持简洁，只沉淀长期有效的说明。\n"
        "- `core/` 只放需要更新的源码仓库，不放报告和文档。\n"
        "- `reference/` 只放参考材料，不直接承载要修改的主仓库。\n"
        f"{appendix}"
    )


def _render_memory_md(
    chattool_repo_name: str | None,
    language: str,
) -> str:
    if language == "en":
        chattool_line = (
            f"- ChatTool repository: `{chattool_repo_name}`\n"
            if chattool_repo_name
            else ""
        )
        return (
            "# Workspace Memory\n\n"
            "Read this file after `AGENTS.md`. It stores high-priority cross-session context ahead of ordinary task details.\n\n"
            "## Current Workspace\n\n"
            f"{chattool_line}"
            "- Reports root: `reports/`\n"
            "- Task playgrounds root: `playgrounds/`\n"
            "- Core repositories root: `core/`\n"
            "- Reference materials root: `reference/`\n"
            "- Durable status notes: `docs/memory/`\n"
            "- Skills notes: `docs/skills/`\n\n"
            "## Must-Read Notes\n\n"
            "- Active projects:\n"
            "- Long-lived constraints:\n"
            "- Current collaboration preferences:\n"
            "- Release / deployment cautions:\n"
            "- Important local environment notes:\n"
        )
    chattool_line = (
        f"- ChatTool 仓库：`{chattool_repo_name}`\n" if chattool_repo_name else ""
    )
    return (
        "# Workspace Memory\n\n"
        "读完 `AGENTS.md` 后，再读这个文件。这里保留跨 session 的高优先级上下文，优先于普通任务信息。\n\n"
        "## 当前 Workspace\n\n"
        f"{chattool_line}"
        "- 汇报根目录：`reports/`\n"
        "- 任务工作区根目录：`playgrounds/`\n"
        "- 核心仓库目录：`core/`\n"
        "- 参考资料目录：`reference/`\n"
        "- 持久状态记录目录：`docs/memory/`\n"
        "- 技能沉淀目录：`docs/skills/`\n\n"
        "## 必读备注\n\n"
        "- 当前活跃项目：\n"
        "- 长期约束：\n"
        "- 当前协作偏好：\n"
        "- 发布 / 部署注意事项：\n"
        "- 重要本地环境说明：\n"
    )


def _render_reports_readme(language: str) -> str:
    if language == "en":
        return (
            "# Reports\n\n"
            "`reports/` stores human-facing progress and results only.\n\n"
            "- `task`: use `reports/MM-DD-<task-name>/` for one standalone objective. Each task directory should at least contain `TASK.md`, `progress.md`, and `SUMMARY.md`.\n"
            "- `taskset`: use `reports/MM-DD-<set-name>/` for a long-running series around one larger goal. The task-set root may include `TASKSET.md`, a shared `progress.md`, and per-task subdirectories.\n"
        )
    return (
        "# Reports\n\n"
        "`reports/` 只放面向人的进展和结果。\n\n"
        "- `task`：对应一次独立目标，使用 `reports/MM-DD-<task-name>/`。每个任务目录至少包含 `TASK.md`、`progress.md` 和 `SUMMARY.md`。\n"
        "- `taskset`：对应围绕同一大目标持续推进的一组任务，使用 `reports/MM-DD-<set-name>/`。任务集根目录可以包含 `TASKSET.md`、共享 `progress.md` 和子任务目录。\n"
    )


def _render_playgrounds_readme(language: str) -> str:
    if language == "en":
        return (
            "# Playgrounds\n\n"
            "`playgrounds/` stores working materials, drafts, experiments, scripts, and intermediate files.\n\n"
            "- `task`: use `playgrounds/<task-name>/`.\n"
            "- `taskset`: use `playgrounds/task-sets/<set-name>/` as the shared work root, and split into per-task subdirectories when needed.\n"
        )
    return (
        "# Playgrounds\n\n"
        "`playgrounds/` 用来放工作材料、草稿、实验、脚本和中间文件。\n\n"
        "- `task`：使用 `playgrounds/<task-name>/`。\n"
        "- `taskset`：使用 `playgrounds/task-sets/<set-name>/` 作为共享工作根，并按需要继续拆分子任务目录。\n"
    )


def _render_docs_readme(language: str) -> str:
    if language == "en":
        return (
            "# Docs\n\n"
            "`docs/` stores concise durable notes outside source repositories. Use `memory/`, `skills/`, and `tools/` based on note type.\n"
        )
    return (
        "# Docs\n\n"
        "`docs/` 用于沉淀源码仓库之外的简洁长期文档。按内容类型分别放入 `memory/`、`skills/`、`tools/`。\n"
    )


def _render_docs_memory_readme(language: str) -> str:
    if language == "en":
        return (
            "# Memory\n\n"
            "Use this directory for durable status notes and key workspace context that should survive across tasks.\n"
        )
    return "# Memory\n\n这个目录用于保存跨任务保留的状态说明和关键 workspace 上下文。\n"


def _render_docs_skills_readme(language: str) -> str:
    if language == "en":
        return (
            "# Skills\n\n"
            "Use this directory for reusable techniques, copied skills, and per-skill `experience/` notes.\n"
        )
    return (
        "# Skills\n\n"
        "这个目录用于保存可复用技巧、同步出来的 skills，以及各 skill 的 `experience/` 记录。\n"
    )


def _render_docs_tools_readme(language: str) -> str:
    if language == "en":
        return (
            "# Tools\n\n"
            "Use this directory for tool-specific usage notes, pitfalls, and small operational references.\n"
        )
    return "# Tools\n\n这个目录用于保存工具相关的使用说明、踩坑记录和小型操作参考。\n"


def _render_readme(title: str, description: str) -> str:
    return f"# {title}\n\n{description}\n"


def _base_file_map(
    workspace_dir: Path,
    profile: WorkspaceProfile,
    language: str,
    with_chattool: bool,
) -> dict[str, str]:
    repo_name = "ChatTool" if with_chattool else None
    file_map = {
        "AGENTS.md": _render_agents_md(
            workspace_dir, profile, language, with_chattool=with_chattool
        ),
        "MEMORY.md": _render_memory_md(repo_name, language),
        "TODO.md": _render_readme(
            "TODO",
            "Human draft area for rough notes, pending items, and ideas."
            if language == "en"
            else "给人的草稿区，用于记录想法、待办和未整理事项。",
        ),
        "reports/README.md": _render_reports_readme(language),
        "playgrounds/README.md": _render_playgrounds_readme(language),
        "docs/README.md": _render_docs_readme(language),
        "docs/memory/README.md": _render_docs_memory_readme(language),
        "docs/skills/README.md": _render_docs_skills_readme(language),
        "docs/tools/README.md": _render_docs_tools_readme(language),
    }
    if with_chattool:
        file_map["CHATTOOL.md"] = _render_chattool_md(language)
    file_map.update(profile.extra_files(workspace_dir))
    return file_map


def _plan_workspace(
    profile: WorkspaceProfile,
    workspace_dir: Path,
    language: str,
    with_chattool: bool,
) -> tuple[list[Path], dict[Path, str]]:
    dir_paths = [workspace_dir / rel for rel in BASE_DIRS]
    dir_paths.extend(workspace_dir / rel for rel in profile.extra_dirs())
    file_map = _base_file_map(workspace_dir, profile, language, with_chattool)
    planned_files = {workspace_dir / rel: content for rel, content in file_map.items()}
    return dir_paths, planned_files


def _render_dry_run(
    profile: WorkspaceProfile,
    workspace_dir: Path,
    dir_paths: list[Path],
    file_map: dict[Path, str],
    language: str,
    with_chattool: bool,
    chattool_source: str | None,
) -> None:
    if language == "en":
        click.echo("Workspace setup dry run.")
        click.echo(f"Workspace: {workspace_dir}")
        click.echo(f"Profile: {profile.name}")
        click.echo(f"Language: {language}")
        click.echo(f"With ChatTool: {with_chattool}")
        if with_chattool and chattool_source:
            click.echo(f"ChatTool source: {chattool_source}")
        click.echo("Directories:")
    else:
        click.echo("Workspace 初始化预演。")
        click.echo(f"Workspace: {workspace_dir}")
        click.echo(f"Profile: {profile.name}")
        click.echo(f"Language: {language}")
        click.echo(f"With ChatTool: {with_chattool}")
        if with_chattool and chattool_source:
            click.echo(f"ChatTool source: {chattool_source}")
        click.echo("将创建目录：")
    for path in dir_paths:
        click.echo(f"  - {display_path(path, workspace_dir)}")
    click.echo("Files:" if language == "en" else "将写入文件：")
    for path in file_map:
        click.echo(f"  - {display_path(path, workspace_dir)}")


def _select_profile_interactively(default_profile: str = "base") -> str:
    if len(PROFILES) == 1:
        return default_profile
    choices = [
        create_choice(f"{profile.name} - {profile.description}", profile.name)
        for profile in PROFILES.values()
    ]
    selected = ask_select("Select workspace profile", choices=choices)
    if selected == BACK_VALUE:
        raise click.Abort()
    return str(selected or default_profile)


def setup_workspace(
    profile_name=None,
    workspace_dir=None,
    language=None,
    interactive=None,
    force=False,
    dry_run=False,
    with_chattool=False,
    chattool_source=None,
):
    logger.info("Start workspace setup")

    profile_name, workspace_dir = _coerce_profile_and_workspace(
        profile_name, workspace_dir
    )
    language = _resolve_language(language)

    workspace_default = resolve_workspace_dir(workspace_dir=workspace_dir)
    source_default = chattool_source or _default_chattool_source()
    needs_prompt = profile_name is None or workspace_dir is None
    if with_chattool and chattool_source is None:
        needs_prompt = True
    usage = (
        "Usage: chattool setup workspace [PROFILE] [WORKSPACE_DIR] "
        "[--language zh|en] [--with-chattool] [--chattool-source <path-or-url>] "
        "[--force] [--dry-run] [-i|-I]"
    )
    interactive, can_prompt, force_interactive, _, need_prompt = (
        resolve_interactive_mode(
            interactive=interactive,
            auto_prompt_condition=needs_prompt,
        )
    )

    try:
        abort_if_force_without_tty(force_interactive, can_prompt, usage)
    except click.Abort:
        logger.error("Interactive mode requested but no TTY is available")
        raise

    if need_prompt:
        click.echo(
            "Starting interactive workspace setup..."
            if language == "en"
            else "开始交互式初始化 workspace..."
        )
        if profile_name is None:
            profile_name = _select_profile_interactively()
        if workspace_dir is None:
            workspace_value = ask_text("workspace_dir", default=str(workspace_default))
            if workspace_value == BACK_VALUE:
                return
            workspace_dir = workspace_value
        if with_chattool and chattool_source is None:
            source_value = ask_text("chattool_source", default=str(source_default))
            if source_value == BACK_VALUE:
                return
            chattool_source = source_value

    profile = _resolve_profile(profile_name)
    workspace_path = resolve_workspace_dir(workspace_dir=workspace_dir)
    chattool_source = chattool_source or source_default
    dir_paths, file_map = _plan_workspace(
        profile, workspace_path, language, with_chattool=with_chattool
    )

    if dry_run:
        _render_dry_run(
            profile,
            workspace_path,
            dir_paths,
            file_map,
            language,
            with_chattool=with_chattool,
            chattool_source=chattool_source if with_chattool else None,
        )
        return

    workspace_path.mkdir(parents=True, exist_ok=True)
    for path in dir_paths:
        path.mkdir(parents=True, exist_ok=True)

    for path, content in file_map.items():
        write_text_file(path, content, force=force)

    repo_path = None
    copied_skills = []
    repo_action = None
    if with_chattool:
        repo_path, existing_repo, repo_action = _ensure_chattool_repo(
            chattool_source,
            workspace_path,
            force=force,
            interactive=interactive,
            can_prompt=can_prompt,
        )
        skills_source = _workspace_skills_source(repo_path)
        _validate_cloned_repo(skills_source)
        if _should_sync_skills(
            existing_repo=existing_repo, interactive=interactive, can_prompt=can_prompt
        ):
            copied_skills = _copy_skills(
                skills_source,
                workspace_path / "docs" / "skills",
                force=existing_repo or force,
                language=language,
            )
        _maybe_setup_github_auth(interactive=interactive, can_prompt=can_prompt)

    click.echo(
        "Workspace setup completed." if language == "en" else "Workspace 初始化完成。"
    )
    click.echo(f"Workspace: {workspace_path}")
    click.echo(f"Profile: {profile.name}")
    click.echo(f"Language: {language}")
    click.echo(f"With ChatTool: {with_chattool}")
    if repo_path is not None:
        click.echo(f"ChatTool repo: {repo_path}")
        click.echo(f"Repo action: {repo_action}")
        click.echo(f"Skills: {workspace_path / 'docs' / 'skills'}")
        click.echo(f"Copied skills: {len(copied_skills)}")
