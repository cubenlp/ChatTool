from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import click

from chattool.setup.common import display_path, resolve_workspace_dir, write_text_file
from chattool.setup.interactive import (
    abort_if_force_without_tty,
    resolve_interactive_mode,
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

    def setup_md_questions(self) -> list[str]:
        return []


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
    "knowledge",
    "knowledge/blog",
    "knowledge/design",
    "knowledge/memory",
    "knowledge/skills",
    "knowledge/tools",
]


def _today() -> str:
    return date.today().isoformat()


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


def _render_agents_md(
    workspace_dir: Path, profile: WorkspaceProfile, language: str
) -> str:
    appendix = profile.agents_md_appendix(workspace=workspace_dir)
    if language == "en":
        return (
            "# Workspace Agents\n\n"
            "`AGENTS.md` is the entry point for models working in this workspace.\n\n"
            "## Core Principles\n\n"
            "- Progress and results should be reported in `reports/`.\n"
            "- Default to regular-task mode. Use one report directory per task, for example `reports/MM-DD-<task-name>/`.\n"
            "- When work belongs to a long-running series, group it as a task set under `reports/MM-DD-<set-name>/`.\n"
            "- Each regular task report directory should at least contain `TASK.md`, `progress.md`, and `SUMMARY.md`.\n"
            "- Each task set may also keep a shared `progress.md` so the next task can continue from the latest stage.\n"
            "- When multiple tasks run in parallel, both `reports/` and `playgrounds/` must stay task-isolated.\n"
            "- Each task should work inside its own `playgrounds/<task-name>/`.\n"
            "- Task-set work may use a shared root such as `playgrounds/task-sets/<set-name>/` together with per-task subdirectories when needed.\n"
            "- Drafts, experiments, and intermediate artifacts that are not part of human-facing reporting should stay out of `reports/`.\n\n"
            "## Architecture\n\n"
            "```text\n"
            "Human\n"
            "  -> MEMORY.md\n"
            "       -> reports/\n"
            "       -> playgrounds/\n"
            "       -> knowledge/\n\n"
            "Workspace\n"
            "  -> Core project | Reference material\n"
            "```\n\n"
            "This workspace sits around a core project. Collaboration traces stay in the outer workspace so the core project remains clean.\n\n"
            "## Key File Roles\n\n"
            "- `MEMORY.md`: cross-session state. Read it every session before doing substantive work.\n"
            "- `reports/`: human-facing reporting area. Regular tasks use one directory per task; large efforts may use a task-set directory with shared progress.\n"
            "- `playgrounds/`: task-isolated work roots. Regular tasks work in `playgrounds/<task-name>/`; task sets may use `playgrounds/task-sets/<set-name>/`.\n"
            "- `knowledge/`: durable, reusable findings that should accumulate outside the core project.\n\n"
            "## Reports Structure\n\n"
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
            "  <2-task-name>/\n"
            "    TASK.md\n"
            "    progress.md\n"
            "    SUMMARY.md\n"
            "```\n\n"
            "- `TASK.md`: task goal, scope, context, and current judgement.\n"
            "- `progress.md`: stage-by-stage progress and current status.\n"
            "- `SUMMARY.md`: final outcomes and conclusions.\n"
            "- `TASKSET.md`: long-running initiative goal, boundaries, and task breakdown.\n"
            "- Task-set `progress.md`: shared cross-task status so the next task can continue smoothly.\n\n"
            "- For each follow-up task inside a task set, record acceptance requirements at the top of that task's `TASK.md`, including whether unmet conditions should trigger human review or can still be decided by the model. Keep this guidance on the successor task side so predecessor work stays undisturbed.\n\n"
            "## Workflow\n\n"
            "1. Read `MEMORY.md` to load cross-session context and active constraints.\n"
            "2. Default to regular-task mode unless the work is clearly a long-running task series.\n"
            "3. For a regular task, work inside `playgrounds/<task-name>/` and report in `reports/MM-DD-<task-name>/`.\n"
            "4. For a task set, work inside `playgrounds/task-sets/<set-name>/` and report under `reports/MM-DD-<set-name>/<task-name>/`.\n"
            "5. While executing a task, stay focused on that task only.\n"
            "6. During wrap-up, finish the current task report first; if it belongs to a task set, then update the task-set `progress.md` and prepare the next task.\n"
            "7. Write durable findings into `knowledge/` so they accumulate outside the core project.\n"
            "8. Update `MEMORY.md` before ending the session so key context survives.\n\n"
            "## Knowledge Write Rules\n\n"
            "| Situation | Write to |\n"
            "|-----------|----------|\n"
            "| Draft / experiment / temporary work note | `playgrounds/<task-name>/` |\n"
            "| Human-facing task report | `reports/MM-DD-<task-name>/` |\n"
            "| Human-facing task-set overview | `reports/MM-DD-<set-name>/TASKSET.md` and `reports/MM-DD-<set-name>/progress.md` |\n"
            "| Phase summary / exploration | `knowledge/blog/YYYY-MM-DD-topic.md` |\n"
            "| Architecture decision | `knowledge/design/NNN-title.md` |\n"
            "| Status snapshot | `knowledge/memory/YYYY-MM-DD-status.md` |\n"
            "| Tool usage discovery | `knowledge/tools/<toolname>/` |\n"
            "| Reusable technique | `knowledge/skills/` |\n"
            "| Unsure | `knowledge/blog/` first, reorganise later |\n\n"
            "## Conventions\n\n"
            "- `reports/` should only contain task goals, progress updates, summaries, and task-set overviews.\n"
            "- Default to regular-task mode; only create a task set when a series of tasks share one larger initiative.\n"
            "- Keep reports and playgrounds isolated by task to support parallel work safely.\n"
            "- When a task belongs to a task set, close the current task cleanly before moving to the next one.\n"
            "- Do not exceed the current task scope.\n"
            "- Surface uncertainty instead of guessing silently.\n"
            "- Keep the core project clean; workspace protocol and knowledge stay in this scaffold.\n"
            f"{appendix}"
        )
    return (
        "# Workspace Agents\n\n"
        "`AGENTS.md` 是模型进入这个 workspace 后的入口说明。\n\n"
        "## 核心原则\n\n"
        "- 模型的进展和结果，统一在 `reports/` 中汇报。\n"
        "- 默认使用常规任务模式；单个任务的报告按目录整理，例如 `reports/MM-DD-<task-name>/`。\n"
        "- 如果是一组围绕同一目标持续推进的大任务，改用任务集模式，放在 `reports/MM-DD-<set-name>/`。\n"
        "- 每个常规任务目录至少包含 `TASK.md`、`progress.md` 和 `SUMMARY.md`。\n"
        "- 任务集可以额外维护一个全局 `progress.md`，让后续任务直接承接。\n"
        "- 多个任务并行时，`reports/` 和 `playgrounds/` 都按任务隔离。\n"
        "- 每个任务在自己的 `playgrounds/<task-name>/` 里工作。\n"
        "- 任务集可以使用共享工作根，例如 `playgrounds/task-sets/<set-name>/`，并按需要继续拆分子任务目录。\n"
        "- 与汇报无关的草稿、实验和中间材料，不要放进 `reports/`。\n\n"
        "## 架构\n\n"
        "```text\n"
        "Human\n"
        "  -> MEMORY.md\n"
        "       -> reports/\n"
        "       -> playgrounds/\n"
        "       -> knowledge/\n\n"
        "Workspace\n"
        "  -> Core project | Reference material\n"
        "```\n\n"
        "这个 workspace 是包裹核心项目的一层协作脚手架。协作痕迹尽量都留在外层 workspace，核心项目保持干净。\n\n"
        "## 关键文件职责\n\n"
        "- `MEMORY.md`：跨 session 记忆。每次进入工作前都先读。\n"
        "- `reports/`：面向人的汇报区。常规任务按任务目录组织；大任务可以使用任务集目录，并维护共享进展。\n"
        "- `playgrounds/`：模型的工作区根目录。常规任务在 `playgrounds/<task-name>/` 下隔离工作；任务集可以使用 `playgrounds/task-sets/<set-name>/`。\n"
        "- `knowledge/`：可复用知识沉淀区。放研究、设计、经验和说明。\n\n"
        "## Reports 结构\n\n"
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
        "  <2-task-name>/\n"
        "    TASK.md\n"
        "    progress.md\n"
        "    SUMMARY.md\n"
        "```\n\n"
        "- `TASK.md`：任务目标、范围、背景、当前判断。作用更接近任务定义页。\n"
        "- `progress.md`：阶段进展和当前状态。\n"
        "- `SUMMARY.md`：最终结果和结论。\n"
        "- `TASKSET.md`：大任务 / 任务集的目标、边界和任务拆分。\n"
        "- 任务集 `progress.md`：跨任务共享的阶段状态，方便下一个任务直接接续。\n\n"
        "- 任务集中的每个后继任务，建议在该任务自己的 `TASK.md` 开头写清验收需求，并说明不满足时是否触发人类 review，还是允许模型自行决断。这个信息只写在后继任务侧，对前置任务透明，不干扰执行期。\n\n"
        "## 工作流\n\n"
        "1. 先读 `MEMORY.md`，加载跨 session 的背景、约束和当前上下文。\n"
        "2. 默认先判断为常规任务；只有明确是一串围绕同一目标推进的任务，才切换到任务集模式。\n"
        "3. 常规任务在 `playgrounds/<task-name>/` 下工作，并在 `reports/MM-DD-<task-name>/` 下汇报。\n"
        "4. 任务集任务在 `playgrounds/task-sets/<set-name>/` 下工作，并在 `reports/MM-DD-<set-name>/<task-name>/` 下汇报。\n"
        "5. 任务执行过程中，只专注当前任务本身。\n"
        "6. 每次收尾时，先完成当前任务的汇报；如果该任务属于任务集，再更新任务集级 `progress.md`，并衔接下一个任务。\n"
        "7. 把可复用结论写入 `knowledge/`，让知识沉淀留在项目外层。\n"
        "8. 结束前更新 `MEMORY.md`，保留下一次继续工作的必要上下文。\n\n"
        "## 知识写入规则\n\n"
        "| 情况 | 写入位置 |\n"
        "|-----------|----------|\n"
        "| 草稿 / 实验 / 临时工作文档 | `playgrounds/<task-name>/` |\n"
        "| 给人的任务汇报 | `reports/MM-DD-<task-name>/` |\n"
        "| 给人的任务集总览 | `reports/MM-DD-<set-name>/TASKSET.md` 和 `reports/MM-DD-<set-name>/progress.md` |\n"
        "| 阶段总结 / 探索记录 | `knowledge/blog/YYYY-MM-DD-topic.md` |\n"
        "| 架构决策 | `knowledge/design/NNN-title.md` |\n"
        "| 状态快照 | `knowledge/memory/YYYY-MM-DD-status.md` |\n"
        "| 工具使用发现 | `knowledge/tools/<toolname>/` |\n"
        "| 可复用技巧 | `knowledge/skills/` |\n"
        "| 暂时不确定 | 先写到 `knowledge/blog/`，之后再整理 |\n\n"
        "## 约定\n\n"
        "- `reports/` 只承载面向人的目标、阶段进展、最终总结，以及任务集总览。\n"
        "- 默认使用常规任务模式；只有共享同一大目标的一串任务，才建任务集。\n"
        "- `playgrounds/` 也按任务或任务集隔离，避免多任务互相污染。\n"
        "- 如果任务属于任务集，必须先收好当前任务，再进入下一个任务。\n"
        "- 不要超出当前任务边界。\n"
        "- 不确定时要显式暴露，不要默默假设。\n"
        "- 让核心项目保持干净，协议和知识沉淀留在这个 scaffold 中。\n"
        f"{appendix}"
    )


def _render_memory_md(
    workspace_dir: Path, profile: WorkspaceProfile, language: str
) -> str:
    if language == "en":
        return (
            "# Workspace Memory\n\n"
            "## Current workspace / project info\n\n"
            "- Workspace root:\n"
            f"- Profile: `{profile.name}`\n"
            "- Primary project path:\n"
            "- Primary project name:\n"
            "- Project goal:\n\n"
            "## Active tasks\n\n"
            "- \n\n"
            "## Last session date\n\n"
            f"- {_today()}\n\n"
            "## Must-know context\n\n"
            "- \n\n"
            "## Recent decisions\n\n"
            "- \n"
        )
    return (
        "# Workspace Memory\n\n"
        "## 当前 workspace / 项目信息\n\n"
        "- Workspace 根目录:\n"
        f"- Profile: `{profile.name}`\n"
        "- 核心项目路径:\n"
        "- 核心项目名称:\n"
        "- 项目目标:\n\n"
        "## 当前任务列表\n\n"
        "- \n\n"
        "## 上次会话日期\n\n"
        f"- {_today()}\n\n"
        "## 必须知道的上下文\n\n"
        "- \n\n"
        "## 最近决策\n\n"
        "- \n"
    )


def _render_reports_readme(language: str) -> str:
    if language == "en":
        return (
            "# Reports\n\n"
            "Default to regular-task mode: create one directory per task under `reports/MM-DD-<task-name>/`. For long-running initiatives, use `reports/MM-DD-<set-name>/` with `TASKSET.md`, a shared `progress.md`, and per-task subdirectories directly under the set directory.\n"
        )
    return (
        "# Reports\n\n"
        "默认使用常规任务模式：按任务在 `reports/MM-DD-<task-name>/` 下建立目录。若是一组持续推进的大任务，则使用 `reports/MM-DD-<set-name>/`，并维护 `TASKSET.md`、共享 `progress.md` 和该目录下直接展开的子任务目录。\n"
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


def _render_setup_md(profile: WorkspaceProfile, language: str) -> str:
    extra_questions = "\n".join(
        f"   - {question}" for question in profile.setup_md_questions()
    )
    extra_block = f"\n{extra_questions}" if extra_questions else ""
    if language == "en":
        return (
            "# Workspace Setup Checklist\n\n"
            "1. **Discover** — examine the workspace and any linked project: look at directory structure, existing tools, config files, and README files.\n"
            "2. **Ask** — pose clarifying questions to the human before writing anything:\n"
            "   - What is the project name and goal?\n"
            "   - What tools are available and where?\n"
            "   - What is the current top priority?\n"
            "   - Any existing work or state to preserve?"
            f"{extra_block}\n"
            "3. **Adapt** — rewrite `AGENTS.md` and `MEMORY.md` with concrete project-specific content and replace all placeholders.\n"
            "4. **Initialise** — write `knowledge/memory/YYYY-MM-DD-status.md` with the initial project state.\n"
            "5. **Create first task lanes** — default to one regular task in `reports/MM-DD-<task-name>/` and `playgrounds/<task-name>/`; if this is clearly a long-running series, create a task set under `reports/MM-DD-<set-name>/` and `playgrounds/task-sets/<set-name>/` instead.\n"
            "6. **Done** — append `completed: YYYY-MM-DD` to this file.\n"
        )
    return (
        "# Workspace 初始化清单\n\n"
        "1. **Discover** — 检查 workspace 和关联项目：看目录结构、现有工具、配置文件和 README。\n"
        "2. **Ask** — 在写任何内容前，先向人确认关键问题：\n"
        "   - 项目名称和目标是什么？\n"
        "   - 当前可用工具有哪些，分别在哪里？\n"
        "   - 当前最优先的事情是什么？\n"
        "   - 有没有需要保留的现有状态或历史工作？"
        f"{extra_block}\n"
        "3. **Adapt** — 把 `AGENTS.md`、`MEMORY.md` 改成项目相关的具体内容，替换掉所有占位文本。\n"
        "4. **Initialise** — 在 `knowledge/memory/YYYY-MM-DD-status.md` 里写下项目初始状态。\n"
        "5. **Create first task lanes** — 默认创建一个常规任务：`reports/MM-DD-<task-name>/` 和 `playgrounds/<task-name>/`；如果明确是一串长期推进的大任务，则改建 `reports/MM-DD-<set-name>/` 和 `playgrounds/task-sets/<set-name>/`。\n"
        "6. **Done** — 在本文件末尾追加 `completed: YYYY-MM-DD`。\n"
    )


def _render_readme(title: str, description: str) -> str:
    return f"# {title}\n\n{description}\n"


def _base_file_map(
    workspace_dir: Path, profile: WorkspaceProfile, language: str
) -> dict[str, str]:
    if language == "en":
        return {
            "AGENTS.md": _render_agents_md(workspace_dir, profile, language),
            "MEMORY.md": _render_memory_md(workspace_dir, profile, language),
            "setup.md": _render_setup_md(profile, language),
            "reports/README.md": _render_reports_readme(language),
            "playgrounds/README.md": _render_playgrounds_readme(language),
            "knowledge/README.md": _render_readme(
                "Knowledge",
                "Durable model-written knowledge lives here and should stay outside the core project.",
            ),
        }
    return {
        "AGENTS.md": _render_agents_md(workspace_dir, profile, language),
        "MEMORY.md": _render_memory_md(workspace_dir, profile, language),
        "setup.md": _render_setup_md(profile, language),
        "reports/README.md": _render_reports_readme(language),
        "playgrounds/README.md": _render_playgrounds_readme(language),
        "knowledge/README.md": _render_readme(
            "Knowledge", "模型产生的可复用知识沉淀在这里，并且应尽量留在核心项目之外。"
        ),
    }


def _should_protect_setup_md(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return False
    return "completed:" in content


def _plan_workspace(
    profile: WorkspaceProfile, workspace_dir: Path, language: str
) -> tuple[list[Path], dict[Path, str]]:
    dir_paths = [workspace_dir / rel for rel in BASE_DIRS]
    dir_paths.extend(workspace_dir / rel for rel in profile.extra_dirs())
    file_map = _base_file_map(workspace_dir, profile, language)
    file_map.update(profile.extra_files(workspace_dir))
    planned_files = {workspace_dir / rel: content for rel, content in file_map.items()}
    return dir_paths, planned_files


def _render_dry_run(
    profile: WorkspaceProfile,
    workspace_dir: Path,
    dir_paths: list[Path],
    file_map: dict[Path, str],
    language: str,
) -> None:
    if language == "en":
        click.echo("Workspace setup dry run.")
        click.echo(f"Workspace: {workspace_dir}")
        click.echo(f"Profile: {profile.name}")
        click.echo(f"Language: {language}")
        click.echo("Directories:")
    else:
        click.echo("Workspace 初始化预演。")
        click.echo(f"Workspace: {workspace_dir}")
        click.echo(f"Profile: {profile.name}")
        click.echo(f"Language: {language}")
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
):
    logger.info("Start workspace setup")

    profile_name, workspace_dir = _coerce_profile_and_workspace(
        profile_name, workspace_dir
    )
    language = _resolve_language(language)

    workspace_default = resolve_workspace_dir(workspace_dir=workspace_dir)
    needs_prompt = profile_name is None or workspace_dir is None
    usage = "Usage: chattool setup workspace [PROFILE] [WORKSPACE_DIR] [--language zh|en] [--force] [--dry-run] [-i|-I]"
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

    profile = _resolve_profile(profile_name)
    workspace_path = resolve_workspace_dir(workspace_dir=workspace_dir)
    dir_paths, file_map = _plan_workspace(profile, workspace_path, language)

    if dry_run:
        _render_dry_run(profile, workspace_path, dir_paths, file_map, language)
        return

    workspace_path.mkdir(parents=True, exist_ok=True)
    for path in dir_paths:
        path.mkdir(parents=True, exist_ok=True)

    for path, content in file_map.items():
        path_force = force
        if path.name == "setup.md" and _should_protect_setup_md(path):
            path_force = False
        write_text_file(path, content, force=path_force)

    click.echo(
        "Workspace setup completed." if language == "en" else "Workspace 初始化完成。"
    )
    click.echo(f"Workspace: {workspace_path}")
    click.echo(f"Profile: {profile.name}")
    click.echo(f"Language: {language}")
    click.echo(f"Setup guide: {workspace_path / 'setup.md'}")
