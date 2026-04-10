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


def render_docs_skills_readme(language: str) -> str:
    if language == "en":
        return "# Skills\n\nReusable skills, patterns, and practice notes.\n"
    return "# Skills\n\n可复用技巧、skills 与实践记录。\n"


def render_public_readme(language: str) -> str:
    if language == "en":
        return "# Public\n\nThis directory is used for deploying public-facing websites and related publish artifacts.\n"
    return "# Public\n\n这个目录用于部署公开网站及相关发布产物。\n"


def render_memory_md(language: str) -> str:
    if language == "en":
        return (
            "# Workspace Memory\n\n"
            "Read this after `AGENTS.md`. Keep high-priority cross-session context here.\n\n"
            "## Current Workspace\n\n"
            "- Reports root: `reports/`\n"
            "- Task playgrounds root: `playgrounds/`\n"
            "- Core repositories root: `core/`\n"
            "- Reference materials root: `reference/`\n"
            "- Durable status snapshots: `docs/memory/`\n"
            "- Reusable skills notes: `docs/skills/`\n"
            "- Tool-specific notes: `docs/tools/`\n"
            "- Shared imported skills: `skills/`\n"
            "- Public publish root: `public/`\n"
        )
    return (
        "# Workspace Memory\n\n"
        "读完 `AGENTS.md` 后，再读这个文件。这里保留跨 session 的高优先级上下文。\n\n"
        "## 当前 Workspace\n\n"
        "- 汇报根目录：`reports/`\n"
        "- 任务工作区根目录：`playgrounds/`\n"
        "- 核心仓库目录：`core/`\n"
        "- 参考资料目录：`reference/`\n"
        "- 持久状态记录目录：`docs/memory/`\n"
        "- 技能沉淀目录：`docs/skills/`\n"
        "- 工具经验目录：`docs/tools/`\n"
        "- 共享 skills 目录：`skills/`\n"
        "- 对外发布目录：`public/`\n"
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
            "`AGENTS.md` is the entry guide when a model enters this workspace.\n\n"
            "## Core Principles\n\n"
            "- Human-facing progress and outcomes go in `reports/`; drafts and experiments do not.\n"
            "- Tasks are split into `task` and `taskset`. Use `task` by default.\n"
            "- Parallel work must stay isolated in both `reports/` and `playgrounds/`.\n"
            "- Do not invite stage-by-stage review before the task is complete. Finish the work end-to-end first, then report once.\n"
            "- For development tasks, each stage must pass its tests, the docs must be updated, and you must self-review before moving on.\n\n"
            "### task\n\n"
            "- A single independent goal.\n"
            "- Report dir: `reports/MM-DD-<task-name>/`\n"
            "- Work dir: `playgrounds/<task-name>/`\n"
            "- Minimum files: `TASK.md`, `progress.md`, `SUMMARY.md`\n\n"
            "### taskset\n\n"
            "- A series of tasks around one larger goal.\n"
            "- Set dir: `reports/MM-DD-<set-name>/`\n"
            "- Shared work root: `playgrounds/task-sets/<set-name>/`\n"
            "- Keep shared `progress.md` at the set level when helpful.\n\n"
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
            "  skills/\n"
            "  public/\n"
            "```\n\n"
            "This outer workspace keeps collaboration artifacts outside the core repositories.\n\n"
            "## Current Options\n\n"
            f"- Enabled options: `{options_text}`\n"
            "- Source repositories go under `core/`\n"
            "- Reference materials go under `reference/`\n"
            "- Durable notes live under `docs/`\n"
            "- Imported shared skills go under `skills/`\n"
            "- Public publish output goes under `public/`\n\n"
            "## Workflow\n\n"
            "1. Read `MEMORY.md` before starting work.\n"
            "2. Identify the repo to change under `core/` and references under `reference/`.\n"
            "3. Default to `task`; switch to `taskset` only for a long-running grouped objective.\n"
            "4. Work inside the task playground and keep drafts there.\n"
            "5. Update `reports/` only for human-facing goals, progress, and summary.\n"
            "6. At the end, finish the report and update `MEMORY.md` if durable context changed.\n\n"
            "## Write Rules\n\n"
            "| Situation | Write To |\n"
            "|-----------|----------|\n"
            "| Drafts / experiments / temp notes | `playgrounds/<task-name>/` |\n"
            "| Human-facing task report | `reports/MM-DD-<task-name>/` |\n"
            "| Human-facing taskset overview | `reports/MM-DD-<set-name>/TASKSET.md` and `reports/MM-DD-<set-name>/progress.md` |\n"
            "| Repositories to change | `core/<repo-name>/` |\n"
            "| External references / samples | `reference/<topic-or-source>/` |\n"
            "| Durable context snapshots | `docs/memory/YYYY-MM-DD-status.md` |\n"
            "| Tool notes | `docs/tools/<toolname>.md` |\n"
            "| Reusable skills / practice | `docs/skills/` |\n\n"
            "## Conventions\n\n"
            "- Stay within the current task boundary unless the task is explicitly expanded.\n"
            "- State uncertainty explicitly instead of silently assuming.\n"
        )
    return (
        "# Workspace Agents\n\n"
        "`AGENTS.md` 是模型进入这个 workspace 后的入口说明。\n\n"
        "## 核心原则\n\n"
        "- 面向人的进展和结果统一放在 `reports/`，不要把草稿和实验混进去。\n"
        "- 任务分为 `task` 和 `taskset`，默认使用 `task`。\n"
        "- 多任务并行时，`reports/` 和 `playgrounds/` 都必须按任务隔离。\n"
        "- 任务未完成前不要阶段性邀请 review；默认完整做完后再统一汇报结果。\n"
        "- 如果是开发任务，每个阶段都要先测试通过、文档完善，并自行 review 后再继续。\n\n"
        "### task\n\n"
        "- 对应一次独立目标。\n"
        "- 报告目录使用 `reports/MM-DD-<task-name>/`。\n"
        "- 工作目录使用 `playgrounds/<task-name>/`。\n"
        "- 每个任务目录至少包含 `TASK.md`、`progress.md` 和 `SUMMARY.md`。\n\n"
        "### taskset\n\n"
        "- 对应围绕同一大目标持续推进的一组任务。\n"
        "- 任务集目录使用 `reports/MM-DD-<set-name>/`。\n"
        "- 工作根目录使用 `playgrounds/task-sets/<set-name>/`。\n"
        "- 任务集可以维护一个共享 `progress.md`。\n\n"
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
        "  skills/\n"
        "  public/\n"
        "```\n\n"
        "这个 workspace 是包裹源码仓库的一层协作脚手架，协作痕迹尽量留在外层。\n\n"
        "## 当前配置项\n\n"
        f"- 已启用项：`{options_text}`\n"
        "- 需要修改的源码仓库放到 `core/`\n"
        "- 外部参考资料放到 `reference/`\n"
        "- 长期文档放到 `docs/`\n"
        "- 导入的共享 skills 放到 `skills/`\n"
        "- 对外发布产物放到 `public/`\n\n"
        "## 工作流\n\n"
        "1. 开始前先读 `MEMORY.md`。\n"
        "2. 识别当前要改的仓库到 `core/`，把参考资料放到 `reference/`。\n"
        "3. 默认先判断为 `task`；只有长期串行目标才切换到 `taskset`。\n"
        "4. 草稿、实验和中间产物放在对应任务的 `playgrounds/` 下。\n"
        "5. 面向人的目标、进展和总结统一写到 `reports/`。\n"
        "6. 收尾时完成汇报，并在需要时更新 `MEMORY.md`。\n\n"
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
        "- 不要超出当前任务边界；如需扩展，先说明或单独开任务。\n"
        "- 不确定时要显式说明，不要默默假设。\n"
    )


def render_setup_md(
    language: str,
    *,
    existing_workspace: bool,
    helper_agents_path: str | None = None,
    helper_memory_path: str | None = None,
) -> str:
    if language == "en":
        if existing_workspace:
            helper_lines = ""
            if helper_agents_path or helper_memory_path:
                helper_lines = "\nGenerated migration references:\n\n"
                if helper_agents_path:
                    helper_lines += f"- `{helper_agents_path}`\n"
                if helper_memory_path:
                    helper_lines += f"- `{helper_memory_path}`\n"
            return (
                "# setup\n\n"
                "Existing workspace detected. Use this guide to migrate the workspace protocol without interrupting ongoing work."
                f"{helper_lines}\n"
                "## Migration Checklist\n\n"
                "1. Discover\n"
                "Review the current workspace layout, active repos, and existing reporting habits.\n\n"
                "2. Compare\n"
                "Compare the current protocol files with the generated references and decide what should be kept, renamed, or moved.\n\n"
                "3. Adapt\n"
                "Map old directories to the current model: reports for human-facing updates, playgrounds for working files, docs for durable notes, core for source repos, and reference for external material.\n\n"
                "4. Migrate\n"
                "Bring the new AGENTS/MEMORY guidance into the existing workspace carefully. Preserve user content. Move helper notes out of source repos if needed.\n\n"
                "5. Validate\n"
                "For development tasks, make sure each stage has passing tests, updated docs, and a self-review before declaring the migration done. Do not ask for stage review midway.\n\n"
                "6. Clean up\n"
                "After the workspace protocol has been adopted, remove temporary migration helper files and mark completion below.\n\n"
                "completed: <YYYY-MM-DD when migration is fully done>\n"
            )
        return (
            "# setup\n\n"
            "Use this checklist to start a fresh human-AI collaboration workspace.\n\n"
            "## Startup Checklist\n\n"
            "1. Discover\n"
            "Read `AGENTS.md` and `MEMORY.md`. Identify the core repo, references, and delivery goal.\n\n"
            "2. Ask\n"
            "Clarify missing acceptance criteria only when they block execution.\n\n"
            "3. Adapt\n"
            "Decide whether this is a `task` or a `taskset`. Default to `task`.\n\n"
            "4. Initialise\n"
            "Create the matching report and playground directories. Keep drafts in `playgrounds/` and human-facing updates in `reports/`.\n\n"
            "5. Create first task lane\n"
            "Start the first task with explicit scope, acceptance, and artifacts. For development tasks, pass tests, update docs, and self-review each stage before continuing.\n\n"
            "6. Done\n"
            "Finish the work end-to-end before asking for review. Report once with the final result, then update `MEMORY.md` if durable context changed.\n\n"
            "completed: <YYYY-MM-DD when the workspace has been fully adopted>\n"
        )
    if existing_workspace:
        helper_lines = ""
        if helper_agents_path or helper_memory_path:
            helper_lines = "\n本次还生成了迁移参考文件：\n\n"
            if helper_agents_path:
                helper_lines += f"- `{helper_agents_path}`\n"
            if helper_memory_path:
                helper_lines += f"- `{helper_memory_path}`\n"
        return (
            "# setup\n\n"
            "检测到这是一个已有 workspace。使用这份指南把新的协作协议迁移进来，同时尽量不打断现有工作。"
            f"{helper_lines}\n"
            "## 迁移清单\n\n"
            "1. Discover\n"
            "先盘点当前 workspace 的目录结构、活跃仓库、已有汇报方式和长期文档位置。\n\n"
            "2. Compare\n"
            "对照当前协议文件与本次生成的参考文件，判断哪些约定需要保留、合并或迁移。\n\n"
            "3. Adapt\n"
            "把旧结构映射到当前模型：`reports/` 负责面向人的汇报，`playgrounds/` 放过程材料，`docs/` 放长期文档，`core/` 放源码仓库，`reference/` 放外部参考。\n\n"
            "4. Migrate\n"
            "把新版 `AGENTS.md` / `MEMORY.md` 的有效规则迁移到现有 workspace。不要覆盖用户已有内容；必要时先搬运、再精简。\n\n"
            "5. Validate\n"
            "如果迁移涉及开发任务，每个阶段都要先测试通过、文档完善并自行 review；任务未完成前不要阶段性邀请 review。\n\n"
            "6. Clean up\n"
            "迁移完成后，删除本次生成的辅助文件，并在下面补记完成日期。\n\n"
            "completed: <迁移完全完成后填写 YYYY-MM-DD>\n"
        )
    return (
        "# setup\n\n"
        "使用这份清单启动一个新的 human-AI 协作 workspace。\n\n"
        "## 启动清单\n\n"
        "1. Discover\n"
        "先读 `AGENTS.md` 和 `MEMORY.md`，识别核心仓库、参考资料和交付目标。\n\n"
        "2. Ask\n"
        "只有在缺少验收标准且会阻塞执行时，才补问必要信息。\n\n"
        "3. Adapt\n"
        "判断当前更适合 `task` 还是 `taskset`；默认先用 `task`。\n\n"
        "4. Initialise\n"
        "创建对应的 report 和 playground 目录；过程材料留在 `playgrounds/`，面向人的同步写进 `reports/`。\n\n"
        "5. Create first task lane\n"
        "为第一个任务写清范围、验收和产物。如果是开发任务，每个阶段都要先测试通过、更新文档并自行 review，再继续推进。\n\n"
        "6. Done\n"
        "默认完整做完后再统一汇报结果，不在中途阶段性邀请 review；收尾时按需更新 `MEMORY.md`。\n\n"
        "completed: <workspace 完整启用后填写 YYYY-MM-DD>\n"
    )


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
        "setup.md": render_setup_md(
            language,
            existing_workspace=existing_workspace,
            helper_agents_path=helper_agents_path,
            helper_memory_path=helper_memory_path,
        ),
        "reports/README.md": render_reports_readme(language),
        "playgrounds/README.md": render_playgrounds_readme(language),
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
