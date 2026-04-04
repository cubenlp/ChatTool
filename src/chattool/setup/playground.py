from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import click

from chattool.setup.common import display_path as _display_path
from chattool.setup.common import resolve_workspace_dir as _resolve_workspace_dir
from chattool.setup.common import write_text_file as _write_text_file
from chattool.setup.interactive import (
    abort_if_force_without_tty,
    resolve_interactive_mode,
)
from chattool.utils import mask_secret
from chattool.utils.custom_logger import setup_logger
from chattool.utils.tui import BACK_VALUE, ask_confirm, ask_text

logger = setup_logger("setup_playground")

EXPERIENCE_LOG_FORMAT = "date_h_min_标题.log"
DEFAULT_CHATTOOL_REPO_URL = "https://github.com/cubenlp/ChatTool.git"
DEFAULT_CHATTOOL_REPO_DIRNAME = "ChatTool"
LEGACY_CHATTOOL_REPO_DIRNAME = "chattool"
DEFAULT_LANGUAGE = "zh"
SUPPORTED_LANGUAGES = {"zh", "en"}


def _default_chattool_repo_dir() -> Path:
    return Path(__file__).resolve().parents[3]


def _default_chattool_source() -> str:
    repo_dir = _default_chattool_repo_dir().resolve()
    if (repo_dir / ".git").exists():
        return str(repo_dir)
    return DEFAULT_CHATTOOL_REPO_URL


def _preferred_workspace_repo_dir(workspace_dir: Path) -> Path:
    return workspace_dir / DEFAULT_CHATTOOL_REPO_DIRNAME


def _legacy_workspace_repo_dir(workspace_dir: Path) -> Path:
    return workspace_dir / LEGACY_CHATTOOL_REPO_DIRNAME


def _find_existing_workspace_repo_dir(workspace_dir: Path) -> Path | None:
    preferred = _preferred_workspace_repo_dir(workspace_dir)
    if preferred.exists():
        return preferred
    legacy = _legacy_workspace_repo_dir(workspace_dir)
    if legacy.exists():
        return legacy
    return None


def _workspace_repo_dir(workspace_dir: Path) -> Path:
    return _find_existing_workspace_repo_dir(
        workspace_dir
    ) or _preferred_workspace_repo_dir(workspace_dir)


def _resolve_language(language: str | None) -> str:
    key = (language or DEFAULT_LANGUAGE).strip().lower()
    if key not in SUPPORTED_LANGUAGES:
        supported = ", ".join(sorted(SUPPORTED_LANGUAGES))
        raise click.ClickException(
            f"Unknown playground language: {language}. Supported: {supported}"
        )
    return key


def _workspace_skills_source(chattool_repo_dir: Path) -> Path:
    return chattool_repo_dir / "skills"


def _workspace_is_empty(workspace_dir: Path) -> bool:
    return not workspace_dir.exists() or not any(workspace_dir.iterdir())


def _workspace_has_existing_files(workspace_dir: Path) -> bool:
    targets = [
        workspace_dir / "AGENTS.md",
        workspace_dir / "CHATTOOL.md",
        workspace_dir / "MEMORY.md",
        workspace_dir / "thoughts",
        workspace_dir / "reports",
        workspace_dir / "playgrounds",
        workspace_dir / "knowledge",
        workspace_dir / "Memory",
        workspace_dir / "skills",
        workspace_dir / "scratch",
        _preferred_workspace_repo_dir(workspace_dir),
        _legacy_workspace_repo_dir(workspace_dir),
    ]
    return any(target.exists() for target in targets)


def _render_agents_md(
    workspace_dir: Path, chattool_repo_dir: Path, language: str
) -> str:
    repo_display = _display_path(chattool_repo_dir, workspace_dir)
    if language == "en":
        return (
            "# Workspace Agents\n\n"
            "## Overview\n\n"
            f"- Workspace root: `{workspace_dir}`\n"
            f"- ChatTool repo: `{repo_display}`\n"
            "- Must-read durable memory: `MEMORY.md`\n"
            "- Shared project guide: `CHATTOOL.md`\n"
            "- Reports root: `reports/`\n"
            "- Task playgrounds root: `playgrounds/`\n"
            "- Durable knowledge root: `knowledge/`\n"
            "- Workspace skills: `knowledge/skills/`\n\n"
            "## Core Principles\n\n"
            "- Default to regular-task mode. Use `reports/MM-DD-<task-name>/` and `playgrounds/<task-name>/`.\n"
            "- When work belongs to a long-running series, switch to task-set mode under `reports/task-sets/<set-name>/` and `playgrounds/task-sets/<set-name>/`.\n"
            "- Each regular task report directory should at least contain `TASK.md`, `progress.md`, and `SUMMARY.md`.\n"
            "- Task sets may keep a shared `progress.md` so the next task can continue directly.\n"
            "- Multiple active tasks must stay isolated from one another.\n"
            f"- Skill practice logs live under `knowledge/skills/<name>/experience/` and use `{EXPERIENCE_LOG_FORMAT}`.\n"
            "- While executing a task, stay focused on that task only; only during wrap-up should you update shared progress and bridge to the next task.\n\n"
            "## How To Start\n\n"
            "- Read this file first when starting work in this workspace.\n"
            "- Read `MEMORY.md` next for high-priority, must-read context.\n"
            "- Read `CHATTOOL.md` for the project purpose, upgrade loop, and development suggestions.\n"
            "- Read the current task or task-set report before starting or continuing execution work.\n"
            "- Models can explore freely in the workspace, but durable conclusions should be written back into `reports/`, `knowledge/`, or skill experience logs.\n\n"
            "## Workspace Contents\n\n"
            "- `ChatTool/`: cloned ChatTool repository used as the main upgrade target.\n"
            "- `reports/`: human-facing reports for regular tasks and task sets.\n"
            "- `playgrounds/`: task-isolated drafts, experiments, and temporary work.\n"
            "- `knowledge/`: durable memory, skills, tools notes, and reusable conclusions.\n\n"
            "## Development Guidance\n\n"
            "- Put reusable implementation into `ChatTool/src/`.\n"
            "- Put durable task-specific guidance into `ChatTool/skills/` or workspace `knowledge/skills/`.\n"
            "- Keep temporary outputs inside the relevant task playground unless they are intentionally promoted.\n"
            "- After implementation, use `practice-make-perfact` as the post-task normalization phase.\n"
            "- In that post-task phase, explicitly chain `chattool-dev-review` to check development standards.\n"
            f"- Experience logs live under `knowledge/skills/<name>/experience/` and use `{EXPERIENCE_LOG_FORMAT}`.\n"
            "- After a task, update reports, durable memory, relevant skill experience, and then normalize useful improvements back into ChatTool.\n\n"
            "## Workflow\n\n"
            "1. Read `AGENTS.md`, `MEMORY.md`, `CHATTOOL.md`, and the current task or task-set report.\n"
            "2. Default to regular-task mode unless the work is clearly one series of related tasks.\n"
            "3. For a regular task, work in `playgrounds/<task-name>/` and report in `reports/MM-DD-<task-name>/`.\n"
            "4. For a task set, work in `playgrounds/task-sets/<set-name>/` and report in `reports/task-sets/<set-name>/tasks/MM-DD-<task-name>/`.\n"
            "5. During task execution, stay focused on the current task itself.\n"
            "6. During wrap-up, finish the current task report first; if it belongs to a task set, then update the task-set `progress.md` and connect to the next task.\n"
            "7. Update `knowledge/memory/`, `knowledge/skills/`, and ChatTool code or skills when durable improvements emerge.\n\n"
            "## Workspace Notes\n\n"
            "- Current projects:\n"
            "- Preferred branch / PR flow:\n"
            "- Testing expectations:\n"
            "- Release or deployment notes:\n"
            "- Other local conventions:\n"
        )
    return (
        "# Workspace Agents\n\n"
        "## 概览\n\n"
        f"- Workspace 根目录：`{workspace_dir}`\n"
        f"- ChatTool 仓库：`{repo_display}`\n"
        "- 必读长期记忆：`MEMORY.md`\n"
        "- 共享项目说明：`CHATTOOL.md`\n"
        "- 汇报根目录：`reports/`\n"
        "- 任务工作区根目录：`playgrounds/`\n"
        "- 长期知识根目录：`knowledge/`\n"
        "- 工作区 skills：`knowledge/skills/`\n\n"
        "## 核心原则\n\n"
        "- 默认使用常规任务模式，目录约定为 `reports/MM-DD-<task-name>/` 和 `playgrounds/<task-name>/`。\n"
        "- 如果工作明显属于同一长期系列任务，则切到任务集模式，放在 `reports/task-sets/<set-name>/` 和 `playgrounds/task-sets/<set-name>/`。\n"
        "- 每个常规任务目录至少包含 `TASK.md`、`progress.md` 和 `SUMMARY.md`。\n"
        "- 任务集可以维护一个共享 `progress.md`，方便下一个任务直接衔接。\n"
        "- 多个活跃任务之间必须保持隔离。\n"
        f"- Skill 练习日志放在 `knowledge/skills/<name>/experience/`，文件名使用 `{EXPERIENCE_LOG_FORMAT}`。\n"
        "- 执行任务时只专注当前任务；只有在收尾阶段才更新共享进展并衔接下一个任务。\n\n"
        "## 如何开始\n\n"
        "- 在这个 workspace 开始工作时，先读本文件。\n"
        "- 接着读 `MEMORY.md`，加载高优先级、必须知道的上下文。\n"
        "- 再读 `CHATTOOL.md`，理解项目目标、升级循环和开发建议。\n"
        "- 在开始或继续执行前，先读当前任务或任务集的报告。\n"
        "- 模型可以在 workspace 中自由探索，但长期有效的结论应回写到 `reports/`、`knowledge/` 或 skill experience 日志。\n\n"
        "## Workspace 内容\n\n"
        "- `ChatTool/`：clone 下来的 ChatTool 仓库，是主要升级目标。\n"
        "- `reports/`：面向人的常规任务和任务集汇报区。\n"
        "- `playgrounds/`：按任务隔离的草稿、实验和临时工作区。\n"
        "- `knowledge/`：长期记忆、skills、工具笔记和可复用结论。\n\n"
        "## 开发建议\n\n"
        "- 可复用实现尽量写进 `ChatTool/src/`。\n"
        "- 长期有效的任务指导尽量放进 `ChatTool/skills/` 或 workspace 的 `knowledge/skills/`。\n"
        "- 临时产物尽量留在对应任务的 playground，除非你明确要提升为长期资产。\n"
        "- 每次实现完成后，用 `practice-make-perfact` 做任务后整理。\n"
        "- 在整理阶段显式串联 `chattool-dev-review`，检查开发规范。\n"
        f"- Experience 日志统一放在 `knowledge/skills/<name>/experience/`，文件名使用 `{EXPERIENCE_LOG_FORMAT}`。\n"
        "- 任务结束后，更新 reports、长期 memory、相关 skill experience，再把有价值的改进沉淀回 ChatTool。\n\n"
        "## 工作流\n\n"
        "1. 先读 `AGENTS.md`、`MEMORY.md`、`CHATTOOL.md` 和当前任务或任务集报告。\n"
        "2. 默认使用常规任务模式；只有明确是一串相关任务时才切到任务集模式。\n"
        "3. 常规任务在 `playgrounds/<task-name>/` 工作，并在 `reports/MM-DD-<task-name>/` 汇报。\n"
        "4. 任务集任务在 `playgrounds/task-sets/<set-name>/` 工作，并在 `reports/task-sets/<set-name>/tasks/MM-DD-<task-name>/` 汇报。\n"
        "5. 任务执行中只专注当前任务本身。\n"
        "6. 收尾时先完成当前任务报告；如果它属于任务集，再更新任务集 `progress.md` 并衔接下一个任务。\n"
        "7. 当出现长期有效的改进时，更新 `knowledge/memory/`、`knowledge/skills/` 以及 ChatTool 代码或 skills。\n\n"
        "## Workspace 备注\n\n"
        "- 当前项目：\n"
        "- 偏好的分支 / PR 流程：\n"
        "- 测试要求：\n"
        "- 发布或部署注意事项：\n"
        "- 其他本地约定：\n"
    )


def _render_chattool_md(
    workspace_dir: Path, chattool_repo_dir: Path, language: str
) -> str:
    repo_display = _display_path(chattool_repo_dir, workspace_dir)
    if language == "en":
        return (
            "# ChatTool Workspace Guide\n\n"
            "This workspace treats the ChatTool checkout as an evolving capability source for many models.\n\n"
            "## Layout\n\n"
            f"- ChatTool repo clone: `{repo_display}`\n"
            "- Shared instructions: `AGENTS.md`\n"
            "- Must-read memory summary: `MEMORY.md`\n"
            "- Reports root: `reports/`\n"
            "- Task playgrounds root: `playgrounds/`\n"
            "- Shared memory root: `knowledge/memory/`\n"
            "- Shared skills copies: `knowledge/skills/`\n\n"
            "## Purpose\n\n"
            "- Use ChatTool as an upgrade surface for setup flows, skills, CLI helpers, and model-facing automation.\n"
            "- Let multiple models work in the same workspace with task isolation, shared context, and reusable lessons.\n"
            "- Promote reusable improvements back into the ChatTool repository instead of leaving them as one-off notes.\n\n"
            "## Suggested Development Loop\n\n"
            "1. Start from one concrete task in the workspace.\n"
            "2. Default to a regular task unless this work is clearly part of a longer task series.\n"
            "3. Explore in the task playground and the cloned ChatTool checkout.\n"
            "4. After the task, update reports and `knowledge/memory/` if context should survive future sessions.\n"
            f"5. Add practice notes under `knowledge/skills/<name>/experience/` using `{EXPERIENCE_LOG_FORMAT}`.\n"
            "6. Periodically review those logs and use `practice-make-perfact` plus `chattool-dev-review` to fold durable improvements back into ChatTool.\n\n"
            "## Development Suggestions\n\n"
            "- Keep scratch experiments and temporary exports outside repositories when possible.\n"
            "- Put reusable implementation in `ChatTool/src/chattool/`.\n"
            "- Keep task-specific guidance in `knowledge/skills/` or `ChatTool/skills/`, not in random scratch files.\n"
            "- Prefer `chattool gh` for PR and CI workflows once changes are ready.\n"
        )
    return (
        "# ChatTool Workspace 指南\n\n"
        "这个 workspace 把 ChatTool checkout 作为多个模型共同演进能力的核心来源。\n\n"
        "## 布局\n\n"
        f"- ChatTool 仓库副本：`{repo_display}`\n"
        "- 共享协作说明：`AGENTS.md`\n"
        "- 必读记忆摘要：`MEMORY.md`\n"
        "- 汇报根目录：`reports/`\n"
        "- 任务工作区根目录：`playgrounds/`\n"
        "- 共享记忆根目录：`knowledge/memory/`\n"
        "- 共享 skills 副本：`knowledge/skills/`\n\n"
        "## 目的\n\n"
        "- 把 ChatTool 作为 setup 流程、skills、CLI 辅助能力和面向模型自动化的升级面。\n"
        "- 让多个模型能在同一 workspace 里协作，同时保持任务隔离、共享上下文和可复用经验。\n"
        "- 把有复用价值的改进回流到 ChatTool 仓库，而不是只留下临时笔记。\n\n"
        "## 建议开发循环\n\n"
        "1. 从 workspace 中一个具体任务开始。\n"
        "2. 默认使用常规任务模式；只有明确属于长期任务序列时才切到任务集。\n"
        "3. 在任务 playground 和 clone 下来的 ChatTool 仓库中探索和实现。\n"
        "4. 任务结束后，如果上下文需要跨 session 保留，则更新 reports 和 `knowledge/memory/`。\n"
        f"5. 在 `knowledge/skills/<name>/experience/` 下记录 practice 笔记，文件名使用 `{EXPERIENCE_LOG_FORMAT}`。\n"
        "6. 定期回顾这些日志，并用 `practice-make-perfact` 加上 `chattool-dev-review` 把长期有效的改进沉淀回 ChatTool。\n\n"
        "## 开发建议\n\n"
        "- 草稿实验和临时导出尽量放在仓库之外或对应任务工作区里。\n"
        "- 可复用实现尽量写进 `ChatTool/src/chattool/`。\n"
        "- 任务特定但可长期复用的指导放在 `knowledge/skills/` 或 `ChatTool/skills/`，不要散落在临时文件中。\n"
        "- 代码准备好后，优先用 `chattool gh` 处理 PR 和 CI 流程。\n"
    )


def _render_reports_readme(language: str) -> str:
    if language == "en":
        return (
            "# Reports\n\n"
            "Default to regular-task mode: create one directory per task under `reports/MM-DD-<task-name>/`. For long-running initiatives, use `reports/task-sets/<set-name>/` with `TASKSET.md`, a shared `progress.md`, and task-specific directories under `tasks/`.\n"
        )
    return (
        "# Reports\n\n"
        "默认使用常规任务模式：按任务在 `reports/MM-DD-<task-name>/` 下建立目录。若是一组持续推进的大任务，则使用 `reports/task-sets/<set-name>/`，并维护 `TASKSET.md`、共享 `progress.md` 和 `tasks/` 下的子任务目录。\n"
    )


def _render_playgrounds_readme(language: str) -> str:
    if language == "en":
        return (
            "# Playgrounds\n\n"
            "Regular tasks use `playgrounds/<task-name>/` for drafts, experiments, scripts, and intermediate files. Task sets may use `playgrounds/task-sets/<set-name>/` as a shared working root and add per-task subdirectories when needed.\n"
        )
    return (
        "# Playgrounds\n\n"
        "常规任务把草稿、实验、脚本和中间文件放在 `playgrounds/<task-name>/` 下。任务集可以使用 `playgrounds/task-sets/<set-name>/` 作为共享工作根，并按需要继续拆分子任务目录。\n"
    )


def _render_knowledge_readme(language: str) -> str:
    if language == "en":
        return (
            "# Knowledge\n\n"
            "Durable memory, copied skills, tool notes, and reusable conclusions live here so the outer workspace can stay useful across many tasks and many models.\n"
        )
    return (
        "# Knowledge\n\n"
        "长期记忆、复制过来的 skills、工具笔记和可复用结论都沉淀在这里，让外层 workspace 能在多任务、多模型协作下持续可用。\n"
    )


def _render_memory_readme(language: str) -> str:
    if language == "en":
        return (
            "# Memory\n\n"
            "Use this directory for durable workspace memory that should survive across tasks and task sets.\n\n"
            "Suggested contents:\n\n"
            "- recurring project context\n"
            "- stable environment notes\n"
            "- long-lived decisions\n"
            "- links to important skills or experience logs\n"
        )
    return (
        "# Memory\n\n"
        "这个目录用于保存会跨任务、跨任务集持续保留的 workspace 记忆。\n\n"
        "建议内容：\n\n"
        "- 会反复出现的项目背景\n"
        "- 稳定的环境说明\n"
        "- 长期生效的决策\n"
        "- 重要 skills 或 experience 日志的索引\n"
    )


def _render_memory_md(
    workspace_dir: Path, chattool_repo_dir: Path, language: str
) -> str:
    repo_display = _display_path(chattool_repo_dir, workspace_dir)
    if language == "en":
        return (
            "# Workspace Memory\n\n"
            "Read this file after `AGENTS.md`. It is reserved for high-priority context that should be loaded before ordinary task work.\n\n"
            "## Current Workspace\n\n"
            f"- ChatTool repo clone: `{repo_display}`\n"
            "- Reports root: `reports/`\n"
            "- Task playgrounds root: `playgrounds/`\n"
            "- Durable notes directory: `knowledge/memory/`\n"
            "- Skills copies directory: `knowledge/skills/`\n\n"
            "## Must-Read Notes\n\n"
            "- Active projects:\n"
            "- Long-lived constraints:\n"
            "- Current collaboration preferences:\n"
            "- Release / deployment cautions:\n"
            "- Important local environment notes:\n"
        )
    return (
        "# Workspace Memory\n\n"
        "在 `AGENTS.md` 之后阅读本文件。这里保留的是在进入日常任务前必须优先加载的上下文。\n\n"
        "## 当前 Workspace\n\n"
        f"- ChatTool 仓库副本：`{repo_display}`\n"
        "- 汇报根目录：`reports/`\n"
        "- 任务工作区根目录：`playgrounds/`\n"
        "- 长期笔记目录：`knowledge/memory/`\n"
        "- Skills 副本目录：`knowledge/skills/`\n\n"
        "## 必读事项\n\n"
        "- 当前活跃项目：\n"
        "- 长期约束：\n"
        "- 当前协作偏好：\n"
        "- 发布 / 部署注意事项：\n"
        "- 重要本地环境说明：\n"
    )


def _render_memory_projects(language: str) -> str:
    if language == "en":
        return (
            "# Projects\n\n"
            "Track active or recurring workspace projects here.\n\n"
            "Suggested sections:\n\n"
            "- project name\n"
            "- current goals\n"
            "- main repo or paths\n"
            "- preferred models or skills\n"
            "- current blockers\n"
        )
    return (
        "# Projects\n\n"
        "在这里追踪当前活跃或会反复出现的 workspace 项目。\n\n"
        "建议字段：\n\n"
        "- 项目名称\n"
        "- 当前目标\n"
        "- 主要仓库或路径\n"
        "- 推荐使用的模型或 skills\n"
        "- 当前阻塞点\n"
    )


def _render_memory_decisions(language: str) -> str:
    if language == "en":
        return (
            "# Decisions\n\n"
            "Use this file for durable decisions that should remain true across many sessions.\n\n"
            "Suggested entries:\n\n"
            "- date\n"
            "- decision\n"
            "- rationale\n"
            "- impact\n"
        )
    return (
        "# Decisions\n\n"
        "用这个文件记录那些会跨很多 session 持续成立的长期决策。\n\n"
        "建议字段：\n\n"
        "- 日期\n"
        "- 决策\n"
        "- 原因\n"
        "- 影响\n"
    )


def _render_memory_logs_readme(language: str) -> str:
    if language == "en":
        return (
            "# Workspace Logs\n\n"
            "Use this directory for general workspace logs that are not specific to a single skill.\n\n"
            f"Suggested filename format: `{EXPERIENCE_LOG_FORMAT}`\n"
        )
    return (
        "# Workspace Logs\n\n"
        "这个目录用于存放不属于单个 skill 的通用 workspace 日志。\n\n"
        f"建议文件名格式：`{EXPERIENCE_LOG_FORMAT}`\n"
    )


def _render_memory_retros_readme(language: str) -> str:
    if language == "en":
        return (
            "# Retros\n\n"
            "Use this directory for periodic retrospectives across tasks, models, and workflows.\n\n"
            "Suggested focus:\n\n"
            "- what is working well\n"
            "- repeated failures or friction\n"
            "- candidate skill updates\n"
            "- candidate ChatTool upgrades\n"
        )
    return (
        "# Retros\n\n"
        "这个目录用于按周期复盘跨任务、跨模型和跨工作流的协作情况。\n\n"
        "建议关注：\n\n"
        "- 哪些地方运行良好\n"
        "- 重复出现的失败或摩擦\n"
        "- 候选 skill 更新\n"
        "- 候选 ChatTool 升级点\n"
    )


def _render_skills_readme(language: str) -> str:
    if language == "en":
        return (
            "# Workspace Skills\n\n"
            "This directory holds workspace-local copies of ChatTool skills.\n\n"
            "Guidelines:\n\n"
            "- Treat copied skills as the workspace-facing layer.\n"
            "- Keep per-skill practice logs under `experience/`.\n"
            f"- Experience logs should use `{EXPERIENCE_LOG_FORMAT}`.\n"
            "- Periodically review useful experience and promote durable improvements back into the ChatTool repo.\n"
        )
    return (
        "# Workspace Skills\n\n"
        "这个目录保存 ChatTool skills 在当前 workspace 中的本地副本。\n\n"
        "约定：\n\n"
        "- 把复制过来的 skills 视为面向 workspace 的使用层。\n"
        "- 每个 skill 的 practice 日志都放在 `experience/` 下。\n"
        f"- Experience 日志文件名应使用 `{EXPERIENCE_LOG_FORMAT}`。\n"
        "- 定期回顾有价值的经验，并把长期有效的改进回流到 ChatTool 仓库。\n"
    )


def _render_scratch_readme(language: str) -> str:
    if language == "en":
        return (
            "# Scratch\n\n"
            "Use this directory for temporary exploration artifacts, drafts, and disposable exports.\n\n"
            "Guidelines:\n\n"
            "- do not treat this as durable memory\n"
            "- move only intentionally preserved outcomes back into `knowledge/memory/`, `knowledge/skills/`, or `ChatTool/`\n"
            "- clean up stale files during periodic retrospectives\n"
        )
    return (
        "# Scratch\n\n"
        "这个目录用于存放临时探索产物、草稿和可丢弃的导出文件。\n\n"
        "约定：\n\n"
        "- 不要把这里当作长期记忆\n"
        "- 只有明确需要保留的结果才回写到 `knowledge/memory/`、`knowledge/skills/` 或 `ChatTool/`\n"
        "- 在周期性复盘时清理陈旧文件\n"
    )


def _render_experience_readme(skill_name: str, language: str) -> str:
    if language == "en":
        return (
            f"# {skill_name} Experience\n\n"
            "Record practice logs for this skill here.\n\n"
            f"Filename format: `{EXPERIENCE_LOG_FORMAT}`\n\n"
            "Suggested log content:\n\n"
            "- task context\n"
            "- what worked\n"
            "- what failed\n"
            "- candidate updates for the skill or ChatTool repo\n"
        )
    return (
        f"# {skill_name} Experience\n\n"
        "在这里记录这个 skill 的 practice 日志。\n\n"
        f"文件名格式：`{EXPERIENCE_LOG_FORMAT}`\n\n"
        "建议记录：\n\n"
        "- 任务上下文\n"
        "- 哪些做法有效\n"
        "- 哪些做法失败\n"
        "- 对 skill 或 ChatTool 仓库的候选改进\n"
    )


def _copy_file(src: Path, dst: Path, force: bool) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and not force:
        logger.info(f"Skip existing skill file: {dst}")
        return "skipped"
    action = "updated" if dst.exists() else "created"
    shutil.copy2(src, dst)
    logger.info(f"{action.capitalize()} skill file: {dst}")
    return action


def _copy_skill_tree(src: Path, dst: Path, force: bool) -> None:
    for path in sorted(src.rglob("*")):
        rel = path.relative_to(src)
        if "__pycache__" in rel.parts or "experience" in rel.parts:
            continue
        target = dst / rel
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        _copy_file(path, target, force=force)


def _copy_skills(
    skills_source: Path, skills_target: Path, force: bool, language: str
) -> list[str]:
    copied = []
    skills_target.mkdir(parents=True, exist_ok=True)
    _write_text_file(
        skills_target / "README.md", _render_skills_readme(language), force=force
    )

    for skill_dir in sorted(skills_source.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name.startswith("."):
            continue
        if not (skill_dir / "SKILL.md").exists():
            continue
        target_dir = skills_target / skill_dir.name
        target_dir.mkdir(parents=True, exist_ok=True)
        _copy_skill_tree(skill_dir, target_dir, force=force)
        experience_dir = target_dir / "experience"
        experience_dir.mkdir(parents=True, exist_ok=True)
        _write_text_file(
            experience_dir / "README.md",
            _render_experience_readme(skill_dir.name, language),
            force=False,
        )
        copied.append(skill_dir.name)
    return copied


def _clone_chattool_repo(
    chattool_source: str, workspace_dir: Path, force: bool
) -> Path:
    repo_dir = _preferred_workspace_repo_dir(workspace_dir)
    clone_cmd = ["git", "clone", chattool_source, str(repo_dir)]
    logger.info(f"Cloning ChatTool into workspace: {' '.join(clone_cmd)}")
    result = subprocess.run(clone_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("Failed to clone ChatTool repository")
        click.echo("Failed to clone ChatTool repository.", err=True)
        if result.stderr:
            click.echo(result.stderr.strip(), err=True)
        raise click.Abort()
    return repo_dir


def _run_git(repo_dir: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_dir), *args],
        capture_output=True,
        text=True,
    )


def _is_git_repo(repo_dir: Path) -> bool:
    return (repo_dir / ".git").exists()


def _repo_has_local_changes(repo_dir: Path) -> bool:
    result = _run_git(repo_dir, ["status", "--porcelain"])
    if result.returncode != 0:
        return False
    return bool(result.stdout.strip())


def _update_submodules(repo_dir: Path) -> None:
    result = _run_git(repo_dir, ["submodule", "update", "--init", "--recursive"])
    if result.returncode != 0:
        logger.error(f"Failed to update git submodules under {repo_dir}")
        click.echo("Failed to update git submodules.", err=True)
        stderr = (result.stderr or "").strip()
        if stderr:
            click.echo(stderr, err=True)
        raise click.Abort()
    logger.info(f"Updated git submodules under {repo_dir}")


def _maybe_migrate_legacy_repo_dir(workspace_dir: Path) -> Path | None:
    preferred = _preferred_workspace_repo_dir(workspace_dir)
    legacy = _legacy_workspace_repo_dir(workspace_dir)
    if preferred.exists() or not legacy.exists():
        return _find_existing_workspace_repo_dir(workspace_dir)
    logger.info(f"Migrating legacy workspace repo dir from {legacy} to {preferred}")
    legacy.rename(preferred)
    click.echo(f"Renamed legacy repo dir: {legacy.name} -> {preferred.name}")
    return preferred


def _update_chattool_repo(
    repo_dir: Path,
    chattool_source: str,
    interactive=None,
    can_prompt=False,
) -> str:
    if not _is_git_repo(repo_dir):
        logger.error(f"Existing ChatTool dir is not a git repo: {repo_dir}")
        click.echo(f"Existing ChatTool dir is not a git repo: {repo_dir}", err=True)
        raise click.Abort()

    if _repo_has_local_changes(repo_dir):
        message = (
            f"ChatTool repo has local changes: {repo_dir}\n"
            "Skip repository update and keep the current working tree?"
        )
        if interactive is not False and can_prompt:
            skip_update = ask_confirm(message, default=True)
            if skip_update == BACK_VALUE:
                raise click.Abort()
            if not skip_update:
                click.echo(
                    "Please commit or stash local changes before rerunning the update.",
                    err=True,
                )
                raise click.Abort()
        else:
            logger.info(
                f"Skipping ChatTool repo update because working tree is dirty: {repo_dir}"
            )
            click.echo(
                f"Skipped ChatTool repo update because local changes were detected: {repo_dir}"
            )
        return "skipped"

    fetch_result = _run_git(repo_dir, ["fetch", "--prune", chattool_source])
    if fetch_result.returncode != 0:
        logger.error(f"Failed to fetch ChatTool updates from {chattool_source}")
        click.echo("Failed to fetch ChatTool updates.", err=True)
        stderr = (fetch_result.stderr or "").strip()
        if stderr:
            click.echo(stderr, err=True)
        raise click.Abort()

    merge_result = _run_git(repo_dir, ["merge", "--ff-only", "FETCH_HEAD"])
    if merge_result.returncode != 0:
        logger.error(f"Failed to fast-forward ChatTool repo: {repo_dir}")
        click.echo("Failed to fast-forward ChatTool repo.", err=True)
        stderr = (merge_result.stderr or "").strip()
        if stderr:
            click.echo(stderr, err=True)
        raise click.Abort()

    _update_submodules(repo_dir)
    logger.info(f"Updated existing ChatTool repo: {repo_dir}")
    return "updated"


def _ensure_chattool_repo(
    chattool_source: str,
    workspace_dir: Path,
    force: bool,
    interactive=None,
    can_prompt=False,
) -> tuple[Path, bool, str]:
    migrated_repo = _maybe_migrate_legacy_repo_dir(workspace_dir)
    repo_dir = migrated_repo or _preferred_workspace_repo_dir(workspace_dir)
    repo_preexisted = repo_dir.exists()

    if not repo_preexisted:
        return (
            _clone_chattool_repo(chattool_source, workspace_dir, force=force),
            False,
            "cloned",
        )

    if force and not _is_git_repo(repo_dir):
        logger.info(f"Removing non-git ChatTool dir before reclone: {repo_dir}")
        shutil.rmtree(repo_dir)
        return (
            _clone_chattool_repo(chattool_source, workspace_dir, force=force),
            False,
            "cloned",
        )

    repo_action = _update_chattool_repo(
        repo_dir,
        chattool_source=chattool_source,
        interactive=interactive,
        can_prompt=can_prompt,
    )
    return repo_dir, True, repo_action


def _is_managed_workspace(workspace_dir: Path) -> bool:
    return _workspace_has_existing_files(workspace_dir)


def _validate_workspace_dir(
    workspace_dir: Path, force: bool, interactive=None, can_prompt=False
) -> None:
    if workspace_dir.exists() and not _workspace_is_empty(workspace_dir) and not force:
        if _is_managed_workspace(workspace_dir):
            logger.info(
                f"Detected existing managed workspace, entering update mode: {workspace_dir}"
            )
            return
        message = (
            f"Workspace dir is not empty: {workspace_dir}\n"
            "Continue anyway and keep existing files? Existing generated files will be skipped unless --force is used."
        )
        if interactive is not False and can_prompt:
            proceed = ask_confirm(message, default=True)
            if proceed == BACK_VALUE:
                raise click.Abort()
            if proceed:
                logger.info(f"Proceeding with non-empty workspace dir: {workspace_dir}")
                return
        logger.error(f"Workspace dir must be empty: {workspace_dir}")
        click.echo(
            f"Workspace dir must be empty before bootstrap: {workspace_dir}", err=True
        )
        raise click.Abort()


def _validate_cloned_repo(skills_source: Path) -> None:
    if not skills_source.exists():
        logger.error(f"Cloned ChatTool repo does not contain skills/: {skills_source}")
        click.echo(
            f"Cloned ChatTool repo does not contain skills/: {skills_source}", err=True
        )
        raise click.Abort()


def _get_default_github_token() -> str | None:
    from chattool.config.github import GitHubConfig

    token = GitHubConfig.GITHUB_ACCESS_TOKEN.value
    if token:
        return str(token).strip() or None
    return None


def _configure_github_https_auth(token: str) -> None:
    logger.info("Configuring Git credential store for github.com")
    subprocess.run(
        ["git", "config", "--global", "credential.helper", "store"],
        check=True,
        capture_output=True,
        text=True,
    )
    credential_input = (
        "protocol=https\n"
        "host=github.com\n"
        "username=x-access-token\n"
        f"password={token}\n\n"
    )
    subprocess.run(
        ["git", "credential", "approve"],
        input=credential_input,
        check=True,
        capture_output=True,
        text=True,
    )


def _maybe_setup_github_auth(interactive, can_prompt) -> bool:
    default_token = _get_default_github_token()
    token = default_token

    if interactive is not False and can_prompt:
        token_prompt = "github_token"
        if default_token:
            token_prompt += f" [current: {mask_secret(default_token)}] (leave blank to keep current)"
        else:
            token_prompt += " (leave blank to skip Git HTTPS auth setup)"
        token_input = ask_text(token_prompt, password=True)
        if token_input == BACK_VALUE:
            return False
        if token_input:
            token = token_input.strip()
    elif not token:
        logger.info(
            "Skipping GitHub auth setup because no GITHUB_ACCESS_TOKEN is available"
        )
        return False

    if not token:
        logger.info("Skipping GitHub auth setup because token is empty")
        return False

    try:
        _configure_github_https_auth(token)
    except subprocess.CalledProcessError as exc:
        logger.error("Failed to configure GitHub HTTPS auth")
        click.echo("Failed to configure GitHub HTTPS auth.", err=True)
        stderr = (exc.stderr or "").strip()
        if stderr:
            click.echo(stderr, err=True)
        raise click.Abort() from exc

    logger.info("Configured GitHub HTTPS auth for github.com")
    click.echo("Configured Git HTTPS auth for github.com.")
    return True


def _should_sync_skills(existing_repo: bool, interactive, can_prompt) -> bool:
    if not existing_repo:
        return True
    if interactive is not False and can_prompt:
        sync_skills = ask_confirm(
            "Update workspace skills from the ChatTool repo? This only replaces regular skill files and keeps experience/ untouched.",
            default=True,
        )
        if sync_skills == BACK_VALUE:
            raise click.Abort()
        return bool(sync_skills)
    return True


def setup_playground(
    workspace_dir=None,
    chattool_source=None,
    language=None,
    interactive=None,
    force=False,
):
    logger.info("Start playground setup")

    language = _resolve_language(language)
    workspace_default = _resolve_workspace_dir(workspace_dir=workspace_dir)
    source_default = chattool_source or _default_chattool_source()
    has_existing = _workspace_has_existing_files(workspace_default)
    usage = (
        "Usage: chattool setup playground [--workspace-dir <path>] [--chattool-source <path-or-url>] "
        "[--language zh|en] [--force] [-i|-I]"
    )
    interactive, can_prompt, force_interactive, _, need_prompt = (
        resolve_interactive_mode(
            interactive=interactive,
            auto_prompt_condition=(
                workspace_dir is None or chattool_source is None or has_existing
            ),
        )
    )

    try:
        abort_if_force_without_tty(force_interactive, can_prompt, usage)
    except click.Abort:
        logger.error("Interactive mode requested but no TTY is available")
        raise

    if need_prompt:
        click.echo(
            "Starting interactive playground setup..."
            if language == "en"
            else "开始交互式初始化 playground..."
        )
        workspace_value = ask_text("workspace_dir", default=str(workspace_default))
        if workspace_value == BACK_VALUE:
            return
        source_value = ask_text("chattool_source", default=str(source_default))
        if source_value == BACK_VALUE:
            return
        workspace_dir = workspace_value
        chattool_source = source_value

    workspace_path = _resolve_workspace_dir(workspace_dir=workspace_dir)
    chattool_source = chattool_source or source_default
    _validate_workspace_dir(
        workspace_path,
        force=force,
        interactive=interactive,
        can_prompt=can_prompt,
    )

    logger.info(f"Workspace root: {workspace_path}")
    logger.info(f"ChatTool source: {chattool_source}")
    logger.info(f"Template language: {language}")
    workspace_path.mkdir(parents=True, exist_ok=True)

    repo_path, existing_repo, repo_action = _ensure_chattool_repo(
        chattool_source,
        workspace_path,
        force=force,
        interactive=interactive,
        can_prompt=can_prompt,
    )
    if repo_action == "cloned":
        _update_submodules(repo_path)
    skills_source = _workspace_skills_source(repo_path)
    _validate_cloned_repo(skills_source)

    logger.info(f"Cloned ChatTool repo dir: {repo_path}")
    logger.info(f"Skills source dir: {skills_source}")

    reports_dir = workspace_path / "reports"
    playgrounds_dir = workspace_path / "playgrounds"
    scratch_dir = playgrounds_dir / "scratch"
    knowledge_dir = workspace_path / "knowledge"
    memory_dir = knowledge_dir / "memory"
    logs_dir = memory_dir / "logs"
    retros_dir = memory_dir / "retros"
    skills_dir = knowledge_dir / "skills"
    reports_dir.mkdir(parents=True, exist_ok=True)
    playgrounds_dir.mkdir(parents=True, exist_ok=True)
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    memory_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    retros_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)
    scratch_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Writing workspace guide files")
    _write_text_file(
        workspace_path / "AGENTS.md",
        _render_agents_md(workspace_path, repo_path, language),
        force=force,
    )
    _write_text_file(
        workspace_path / "CHATTOOL.md",
        _render_chattool_md(workspace_path, repo_path, language),
        force=force,
    )
    _write_text_file(
        workspace_path / "MEMORY.md",
        _render_memory_md(workspace_path, repo_path, language),
        force=force,
    )
    _write_text_file(
        reports_dir / "README.md", _render_reports_readme(language), force=force
    )
    _write_text_file(
        playgrounds_dir / "README.md",
        _render_playgrounds_readme(language),
        force=force,
    )
    _write_text_file(
        knowledge_dir / "README.md", _render_knowledge_readme(language), force=force
    )
    _write_text_file(
        memory_dir / "README.md", _render_memory_readme(language), force=force
    )
    _write_text_file(
        memory_dir / "projects.md", _render_memory_projects(language), force=force
    )
    _write_text_file(
        memory_dir / "decisions.md", _render_memory_decisions(language), force=force
    )
    _write_text_file(
        logs_dir / "README.md", _render_memory_logs_readme(language), force=force
    )
    _write_text_file(
        retros_dir / "README.md",
        _render_memory_retros_readme(language),
        force=force,
    )
    _write_text_file(
        scratch_dir / "README.md", _render_scratch_readme(language), force=force
    )

    copied_skills = []
    if _should_sync_skills(
        existing_repo=existing_repo, interactive=interactive, can_prompt=can_prompt
    ):
        logger.info("Copying workspace skills and creating experience directories")
        copied_skills = _copy_skills(
            skills_source, skills_dir, force=existing_repo or force, language=language
        )
    else:
        logger.info("Skipping workspace skills update by user choice")

    logger.info(f"Playground setup completed with {len(copied_skills)} skills")
    click.echo(
        "Playground setup completed." if language == "en" else "Playground 初始化完成。"
    )
    click.echo(f"Workspace: {workspace_path}")
    click.echo(f"ChatTool repo: {repo_path}")
    click.echo(f"Repo action: {repo_action}")
    click.echo(f"Language: {language}")
    click.echo(f"Memory summary: {workspace_path / 'MEMORY.md'}")
    click.echo(f"Reports: {reports_dir}")
    click.echo(f"Playgrounds: {playgrounds_dir}")
    click.echo(f"Knowledge: {knowledge_dir}")
    click.echo(f"Skills: {skills_dir}")
    click.echo(f"Copied skills: {len(copied_skills)}")
    _maybe_setup_github_auth(interactive=interactive, can_prompt=can_prompt)
