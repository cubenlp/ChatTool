from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import click

from chattool.setup.common import display_path, resolve_workspace_dir, write_text_file
from chattool.setup.interactive import abort_if_force_without_tty, resolve_interactive_mode
from chattool.utils.custom_logger import setup_logger
from chattool.utils.tui import BACK_VALUE, ask_select, ask_text, create_choice

logger = setup_logger("setup_workspace")


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
    "base": BaseProfile(name="base", description="General-purpose human-AI collaboration workspace."),
}

BASE_DIRS = [
    "thoughts",
    "tasks",
    "playground",
    "knowledge",
    "knowledge/blog",
    "knowledge/design",
    "knowledge/memory",
    "knowledge/memory/status",
    "knowledge/skills",
    "knowledge/tools",
    "knowledge/report",
]


def _today() -> str:
    return date.today().isoformat()


def _resolve_profile(profile_name: str | None) -> WorkspaceProfile:
    key = (profile_name or "base").strip().lower()
    profile = PROFILES.get(key)
    if profile is None:
        supported = ", ".join(sorted(PROFILES))
        raise click.ClickException(f"Unknown workspace profile: {profile_name}. Supported: {supported}")
    return profile


def _coerce_profile_and_workspace(profile_name, workspace_dir) -> tuple[str | None, str | None]:
    if profile_name and workspace_dir is None:
        candidate = str(profile_name).strip()
        if candidate.lower() not in PROFILES:
            return None, candidate
    return profile_name, workspace_dir


def _render_agents_md(workspace_dir: Path, profile: WorkspaceProfile) -> str:
    appendix = profile.agents_md_appendix(workspace=workspace_dir)
    return (
        "# Workspace Agents\n\n"
        "## Architecture\n\n"
        "```text\n"
        "Human\n"
        "  -> thoughts/current.md · task.md · MEMORY.md\n"
        "       -> AI collaboration layer\n"
        "       -> Tools\n"
        "       -> Core project | Reference material\n"
        "       -> knowledge/\n"
        "```\n\n"
        "This workspace sits around a core project. Protocol files, task state, and accumulated knowledge live here; the core project stays clean.\n\n"
        "## Key File Roles\n\n"
        "- `thoughts/current.md`: human planning surface. Read this first to understand current intent and constraints.\n"
        "- `task.md`: model working surface. Update it in real time while executing.\n"
        "- `MEMORY.md`: cross-session state. Read it every session before doing substantive work.\n"
        "- `knowledge/report/`: primary human review interface for progress updates and results.\n\n"
        "## Workflow\n\n"
        "1. Read `thoughts/current.md` to understand the human's current focus.\n"
        "2. Work in `task.md` while executing the active task.\n"
        "3. Write durable findings into `knowledge/` so they accumulate outside the core project.\n"
        "4. Update `MEMORY.md` before ending the session so key context survives.\n\n"
        "## Knowledge Write Rules\n\n"
        "| Situation | Write to |\n"
        "|-----------|----------|\n"
        "| Phase summary / exploration | `knowledge/blog/YYYY-MM-DD-topic.md` |\n"
        "| Architecture decision | `knowledge/design/NNN-title.md` |\n"
        "| Status snapshot | `knowledge/memory/status/YYYY-MM-DD-status.md` |\n"
        "| Tool usage discovery | `knowledge/tools/<toolname>/` |\n"
        "| Reusable technique | `knowledge/skills/` |\n"
        "| Progress update | `knowledge/report/` |\n"
        "| Unsure | `knowledge/blog/` first, reorganise later |\n\n"
        "## Conventions\n\n"
        "- Do not exceed the current task scope.\n"
        "- Surface uncertainty instead of guessing silently.\n"
        "- Always update `task.md` before ending a session.\n"
        "- Keep the core project clean; workspace protocol and knowledge stay in this scaffold.\n"
        f"{appendix}"
    )


def _render_memory_md(workspace_dir: Path, profile: WorkspaceProfile) -> str:
    return (
        "# Workspace Memory\n\n"
        "## Current workspace / project info\n\n"
        "- Workspace root:\n"
        f"- Profile: `{profile.name}`\n"
        "- Primary project path:\n"
        "- Primary project name:\n"
        "- Project goal:\n\n"
        "## Active task\n\n"
        "- \n\n"
        "## Last session date\n\n"
        f"- {_today()}\n\n"
        "## Must-know context\n\n"
        "- \n\n"
        "## Recent decisions\n\n"
        "- \n"
    )


def _render_task_md() -> str:
    return (
        "# Task\n\n"
        "## Current task\n\n"
        "- \n\n"
        "## Status checklist\n\n"
        "- [ ] Clarify scope\n"
        "- [ ] Execute work\n"
        "- [ ] Write durable findings\n"
        "- [ ] Update memory\n\n"
        "## Progress notes\n\n"
        "- \n\n"
        "## Completed log\n\n"
        "- \n"
    )


def _render_thoughts_current_md() -> str:
    return (
        "# Current Focus\n\n"
        "## Current focus\n\n"
        "- \n\n"
        "## Goals\n\n"
        "- \n\n"
        "## Open questions\n\n"
        "- \n\n"
        "## Notes\n\n"
        "- \n"
    )


def _render_setup_md(profile: WorkspaceProfile) -> str:
    extra_questions = "\n".join(f"   - {question}" for question in profile.setup_md_questions())
    extra_block = f"\n{extra_questions}" if extra_questions else ""
    return (
        "# Workspace Setup Checklist\n\n"
        "1. **Discover** — examine the workspace and any linked project: look at directory structure, existing tools, config files, and README files.\n"
        "2. **Ask** — pose clarifying questions to the human before writing anything:\n"
        "   - What is the project name and goal?\n"
        "   - What tools are available and where?\n"
        "   - What is the current top priority?\n"
        "   - Any existing work or state to preserve?"
        f"{extra_block}\n"
        "3. **Adapt** — rewrite `AGENTS.md`, `MEMORY.md`, and `thoughts/current.md` with concrete project-specific content and replace all placeholders.\n"
        "4. **Initialise** — write `knowledge/memory/status/YYYY-MM-DD-status.md` with the initial project state.\n"
        "5. **Set first task** — write the first concrete task into `task.md`.\n"
        "6. **Done** — append `completed: YYYY-MM-DD` to this file.\n"
    )


def _render_readme(title: str, description: str) -> str:
    return f"# {title}\n\n{description}\n"


def _base_file_map(workspace_dir: Path, profile: WorkspaceProfile) -> dict[str, str]:
    return {
        "AGENTS.md": _render_agents_md(workspace_dir, profile),
        "MEMORY.md": _render_memory_md(workspace_dir, profile),
        "setup.md": _render_setup_md(profile),
        "task.md": _render_task_md(),
        "thoughts/README.md": _render_readme("Thoughts", "Human planning notes live here. `current.md` is the primary human intent surface."),
        "thoughts/current.md": _render_thoughts_current_md(),
        "tasks/README.md": _render_readme("Tasks", "Store task artifacts here, such as `results.jsonl`, checkpoints, and reports."),
        "playground/README.md": _render_readme("Playground", "Use this directory for disposable scripts and experiments."),
        "knowledge/README.md": _render_readme("Knowledge", "Durable model-written knowledge lives here and should stay outside the core project."),
        "knowledge/report/README.md": _render_readme("Reports", "This is the primary human review interface. Update it after each significant task completion."),
    }


def _should_protect_setup_md(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return False
    return "completed:" in content


def _plan_workspace(profile: WorkspaceProfile, workspace_dir: Path) -> tuple[list[Path], dict[Path, str]]:
    dir_paths = [workspace_dir / rel for rel in BASE_DIRS]
    dir_paths.extend(workspace_dir / rel for rel in profile.extra_dirs())
    file_map = _base_file_map(workspace_dir, profile)
    file_map.update(profile.extra_files(workspace_dir))
    planned_files = {workspace_dir / rel: content for rel, content in file_map.items()}
    return dir_paths, planned_files


def _render_dry_run(profile: WorkspaceProfile, workspace_dir: Path, dir_paths: list[Path], file_map: dict[Path, str]) -> None:
    click.echo("Workspace setup dry run.")
    click.echo(f"Workspace: {workspace_dir}")
    click.echo(f"Profile: {profile.name}")
    click.echo("Directories:")
    for path in dir_paths:
        click.echo(f"  - {display_path(path, workspace_dir)}")
    click.echo("Files:")
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


def setup_workspace(profile_name=None, workspace_dir=None, interactive=None, force=False, dry_run=False):
    logger.info("Start workspace setup")

    profile_name, workspace_dir = _coerce_profile_and_workspace(profile_name, workspace_dir)

    workspace_default = resolve_workspace_dir(workspace_dir=workspace_dir)
    needs_prompt = profile_name is None or workspace_dir is None
    usage = (
        "Usage: chattool setup workspace [PROFILE] [WORKSPACE_DIR] [--force] [--dry-run] [-i|-I]"
    )
    interactive, can_prompt, force_interactive, _, need_prompt = resolve_interactive_mode(
        interactive=interactive,
        auto_prompt_condition=needs_prompt,
    )

    try:
        abort_if_force_without_tty(force_interactive, can_prompt, usage)
    except click.Abort:
        logger.error("Interactive mode requested but no TTY is available")
        raise

    if need_prompt:
        click.echo("Starting interactive workspace setup...")
        if profile_name is None:
            profile_name = _select_profile_interactively()
        if workspace_dir is None:
            workspace_value = ask_text("workspace_dir", default=str(workspace_default))
            if workspace_value == BACK_VALUE:
                return
            workspace_dir = workspace_value

    profile = _resolve_profile(profile_name)
    workspace_path = resolve_workspace_dir(workspace_dir=workspace_dir)
    dir_paths, file_map = _plan_workspace(profile, workspace_path)

    if dry_run:
        _render_dry_run(profile, workspace_path, dir_paths, file_map)
        return

    workspace_path.mkdir(parents=True, exist_ok=True)
    for path in dir_paths:
        path.mkdir(parents=True, exist_ok=True)

    for path, content in file_map.items():
        path_force = force
        if path.name == "setup.md" and _should_protect_setup_md(path):
            path_force = False
        write_text_file(path, content, force=path_force)

    click.echo("Workspace setup completed.")
    click.echo(f"Workspace: {workspace_path}")
    click.echo(f"Profile: {profile.name}")
    click.echo(f"Setup guide: {workspace_path / 'setup.md'}")
