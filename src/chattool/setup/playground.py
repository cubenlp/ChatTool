import shutil
import subprocess
from pathlib import Path

import click

from chattool.setup.interactive import abort_if_force_without_tty, resolve_interactive_mode
from chattool.utils import mask_secret
from chattool.utils.custom_logger import setup_logger
from chattool.utils.tui import BACK_VALUE, ask_confirm, ask_text

logger = setup_logger("setup_playground")

EXPERIENCE_LOG_FORMAT = "date_h_min_标题.log"
DEFAULT_CHATTOOL_REPO_URL = "https://github.com/cubenlp/ChatTool.git"
DEFAULT_CHATTOOL_REPO_DIRNAME = "chattool"


def _default_chattool_repo_dir() -> Path:
    return Path(__file__).resolve().parents[3]


def _default_chattool_source() -> str:
    repo_dir = _default_chattool_repo_dir().resolve()
    if (repo_dir / ".git").exists():
        return str(repo_dir)
    return DEFAULT_CHATTOOL_REPO_URL


def _normalize_path(value) -> Path | None:
    if value is None:
        return None
    if isinstance(value, Path):
        return value.expanduser().resolve()
    text = str(value).strip()
    if not text:
        return None
    return Path(text).expanduser().resolve()


def _resolve_workspace_dir(workspace_dir=None) -> Path:
    return _normalize_path(workspace_dir) or Path.cwd().resolve()


def _workspace_repo_dir(workspace_dir: Path) -> Path:
    return workspace_dir / DEFAULT_CHATTOOL_REPO_DIRNAME


def _workspace_skills_source(workspace_dir: Path) -> Path:
    return _workspace_repo_dir(workspace_dir) / "skills"


def _workspace_is_empty(workspace_dir: Path) -> bool:
    return not workspace_dir.exists() or not any(workspace_dir.iterdir())


def _workspace_has_existing_files(workspace_dir: Path) -> bool:
    targets = [
        workspace_dir / "AGENTS.md",
        workspace_dir / "CHATTOOL.md",
        workspace_dir / "Memory",
        workspace_dir / "skills",
        _workspace_repo_dir(workspace_dir),
    ]
    return any(target.exists() for target in targets)


def _display_path(path: Path, workspace_dir: Path) -> str:
    try:
        return str(path.relative_to(workspace_dir))
    except ValueError:
        return str(path)


def _render_agents_md(workspace_dir: Path, chattool_repo_dir: Path) -> str:
    repo_display = _display_path(chattool_repo_dir, workspace_dir)
    return (
        "# Workspace Agents\n\n"
        "## Overview\n\n"
        f"- Workspace root: `{workspace_dir}`\n"
        f"- ChatTool repo: `{repo_display}`\n"
        "- Must-read durable memory: `MEMORY.md`\n"
        "- Shared project guide: `CHATTOOL.md`\n"
        "- Shared memory: `Memory/`\n"
        "- Shared skills: `skills/`\n\n"
        "## How To Start\n\n"
        "- Read this file first when starting work in this workspace.\n"
        "- Read `MEMORY.md` next for high-priority, must-read context.\n"
        "- Read `CHATTOOL.md` for the project purpose, upgrade loop, and development suggestions.\n"
        "- Models can explore freely in the workspace, but durable conclusions should be written back into memory or skills experience logs.\n"
        "\n"
        "## Workspace Contents\n\n"
        "- `chattool/`: cloned ChatTool repository used as the main upgrade target.\n"
        "- `Memory/`: durable notes, decisions, logs, and retrospectives for the workspace.\n"
        "- `skills/`: workspace-local skill copies used during exploration and execution.\n"
        "- `scratch/`: disposable outputs and temporary exploration material.\n\n"
        "## Development Guidance\n\n"
        "- Put reusable implementation into `chattool/src/`.\n"
        "- Put durable task-specific guidance into `chattool/skills/` or workspace `skills/`.\n"
        "- Keep scratch outputs out of the repository unless they are intentionally promoted.\n"
        "- After implementation, use `practice-make-perfact` as the post-task normalization phase.\n"
        "- In that post-task phase, explicitly chain `chattool-dev-review` to check development standards.\n"
        f"- Experience logs live under `skills/<name>/experience/` and use `{EXPERIENCE_LOG_FORMAT}`.\n"
        "- After a task, update durable memory, relevant skill experience, and then normalize useful improvements back into ChatTool.\n\n"
        "## Workspace Notes\n\n"
        "- Current projects:\n"
        "- Preferred branch / PR flow:\n"
        "- Testing expectations:\n"
        "- Release or deployment notes:\n"
        "- Other local conventions:\n"
    )


def _render_chattool_md(workspace_dir: Path, chattool_repo_dir: Path) -> str:
    repo_display = _display_path(chattool_repo_dir, workspace_dir)
    return (
        "# ChatTool Workspace Guide\n\n"
        "This workspace treats the ChatTool checkout as an evolving capability source for many models.\n\n"
        "## Layout\n\n"
        f"- ChatTool repo clone: `{repo_display}`\n"
        "- Shared instructions: `AGENTS.md`\n"
        "- Must-read memory summary: `MEMORY.md`\n"
        "- Shared memory: `Memory/`\n"
        "- Shared skills copies: `skills/`\n\n"
        "## Purpose\n\n"
        "- Use ChatTool as an upgrade surface for setup flows, skills, CLI helpers, and model-facing automation.\n"
        "- Let multiple models work in the same workspace with shared context while still preserving useful lessons.\n"
        "- Promote reusable improvements back into the ChatTool repository instead of leaving them as one-off notes.\n\n"
        "## Suggested Development Loop\n\n"
        "1. Start from the concrete task in the workspace.\n"
        "2. Explore in the workspace and the cloned ChatTool checkout.\n"
        "3. After the task, update `Memory/` if context should survive future sessions.\n"
        f"4. Add practice notes under `skills/<name>/experience/` using `{EXPERIENCE_LOG_FORMAT}`.\n"
        "5. Periodically review those logs and use `practice-make-perfact` plus `chattool-dev-review` to fold durable improvements back into ChatTool.\n\n"
        "## Development Suggestions\n\n"
        "- Keep scratch experiments and temporary exports outside repositories when possible.\n"
        "- Put reusable implementation in `src/chattool/`.\n"
        "- Keep task-specific guidance in skills, not in random scratch files.\n"
        "- Prefer `chattool gh` for PR and CI workflows once changes are ready.\n"
    )


def _render_memory_readme() -> str:
    return (
        "# Memory\n\n"
        "Use this directory for durable workspace memory that should survive across tasks.\n\n"
        "Suggested contents:\n\n"
        "- recurring project context\n"
        "- stable environment notes\n"
        "- long-lived decisions\n"
        "- links to important skills or experience logs\n"
    )


def _render_memory_md(workspace_dir: Path, chattool_repo_dir: Path) -> str:
    repo_display = _display_path(chattool_repo_dir, workspace_dir)
    return (
        "# Workspace Memory\n\n"
        "Read this file after `AGENTS.md`. It is reserved for high-priority context that should be loaded before ordinary task work.\n\n"
        "## Current Workspace\n\n"
        f"- ChatTool repo clone: `{repo_display}`\n"
        "- Durable notes directory: `Memory/`\n"
        "- Skills copies directory: `skills/`\n\n"
        "## Must-Read Notes\n\n"
        "- Active projects:\n"
        "- Long-lived constraints:\n"
        "- Current collaboration preferences:\n"
        "- Release / deployment cautions:\n"
        "- Important local environment notes:\n"
    )


def _render_memory_projects() -> str:
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


def _render_memory_decisions() -> str:
    return (
        "# Decisions\n\n"
        "Use this file for durable decisions that should remain true across many sessions.\n\n"
        "Suggested entries:\n\n"
        "- date\n"
        "- decision\n"
        "- rationale\n"
        "- impact\n"
    )


def _render_memory_logs_readme() -> str:
    return (
        "# Workspace Logs\n\n"
        "Use this directory for general workspace logs that are not specific to a single skill.\n\n"
        f"Suggested filename format: `{EXPERIENCE_LOG_FORMAT}`\n"
    )


def _render_memory_retros_readme() -> str:
    return (
        "# Retros\n\n"
        "Use this directory for periodic retrospectives across tasks, models, and workflows.\n\n"
        "Suggested focus:\n\n"
        "- what is working well\n"
        "- repeated failures or friction\n"
        "- candidate skill updates\n"
        "- candidate ChatTool upgrades\n"
    )


def _render_skills_readme() -> str:
    return (
        "# Workspace Skills\n\n"
        "This directory holds workspace-local copies of ChatTool skills.\n\n"
        "Guidelines:\n\n"
        "- Treat copied skills as the workspace-facing layer.\n"
        "- Keep per-skill practice logs under `experience/`.\n"
        f"- Experience logs should use `{EXPERIENCE_LOG_FORMAT}`.\n"
        "- Periodically review useful experience and promote durable improvements back into the ChatTool repo.\n"
    )


def _render_scratch_readme() -> str:
    return (
        "# Scratch\n\n"
        "Use this directory for temporary exploration artifacts, drafts, and disposable exports.\n\n"
        "Guidelines:\n\n"
        "- do not treat this as durable memory\n"
        "- move only intentionally preserved outcomes back into `Memory/`, `skills/`, or `chattool/`\n"
        "- clean up stale files during periodic retrospectives\n"
    )


def _render_experience_readme(skill_name: str) -> str:
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


def _write_text_file(path: Path, content: str, force: bool) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        logger.info(f"Skip existing file: {path}")
        return "skipped"
    action = "updated" if path.exists() else "created"
    path.write_text(content, encoding="utf-8")
    logger.info(f"{action.capitalize()} file: {path}")
    return action


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


def _copy_skills(skills_source: Path, skills_target: Path, force: bool) -> list[str]:
    copied = []
    skills_target.mkdir(parents=True, exist_ok=True)
    _write_text_file(skills_target / "README.md", _render_skills_readme(), force=force)

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
        _write_text_file(experience_dir / "README.md", _render_experience_readme(skill_dir.name), force=force)
        copied.append(skill_dir.name)
    return copied


def _clone_chattool_repo(chattool_source: str, workspace_dir: Path, force: bool, interactive=None, can_prompt=False) -> Path:
    repo_dir = _workspace_repo_dir(workspace_dir)
    if repo_dir.exists():
        if force:
            logger.info(f"Removing existing cloned repo: {repo_dir}")
            shutil.rmtree(repo_dir)
        elif interactive is not False and can_prompt:
            skip_clone = ask_confirm(
                (
                    f"ChatTool repo already exists: {repo_dir}\n"
                    "Skip cloning and keep the local ChatTool version?"
                ),
                default=True,
            )
            if skip_clone == BACK_VALUE:
                raise click.Abort()
            if skip_clone:
                logger.info(f"Skipping clone and reusing existing ChatTool repo: {repo_dir}")
                return repo_dir
            logger.info(f"User declined reusing existing ChatTool repo without --force: {repo_dir}")
            click.echo(
                f"Skipped because ChatTool repo already exists: {repo_dir}\n"
                "Use --force if you want to replace the existing clone.",
                err=True,
            )
            raise click.Abort()
        else:
            logger.error(f"ChatTool clone target already exists: {repo_dir}")
            click.echo(f"ChatTool clone target already exists: {repo_dir}", err=True)
            raise click.Abort()

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


def _validate_workspace_dir(workspace_dir: Path, force: bool, interactive=None, can_prompt=False) -> None:
    if workspace_dir.exists() and not _workspace_is_empty(workspace_dir) and not force:
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
        click.echo(f"Workspace dir must be empty before bootstrap: {workspace_dir}", err=True)
        raise click.Abort()


def _validate_cloned_repo(skills_source: Path) -> None:
    if not skills_source.exists():
        logger.error(f"Cloned ChatTool repo does not contain skills/: {skills_source}")
        click.echo(f"Cloned ChatTool repo does not contain skills/: {skills_source}", err=True)
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
        logger.info("Skipping GitHub auth setup because no GITHUB_ACCESS_TOKEN is available")
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


def setup_playground(workspace_dir=None, chattool_source=None, interactive=None, force=False):
    logger.info("Start playground setup")

    workspace_default = _resolve_workspace_dir(workspace_dir=workspace_dir)
    source_default = chattool_source or _default_chattool_source()
    has_existing = _workspace_has_existing_files(workspace_default)
    usage = (
        "Usage: chattool setup playground [--workspace-dir <path>] [--chattool-source <path-or-url>] "
        "[--force] [-i|-I]"
    )
    interactive, can_prompt, force_interactive, _, need_prompt = resolve_interactive_mode(
        interactive=interactive,
        auto_prompt_condition=(workspace_dir is None or chattool_source is None or has_existing),
    )

    try:
        abort_if_force_without_tty(force_interactive, can_prompt, usage)
    except click.Abort:
        logger.error("Interactive mode requested but no TTY is available")
        raise

    if need_prompt:
        click.echo("Starting interactive playground setup...")
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
    workspace_path.mkdir(parents=True, exist_ok=True)

    repo_path = _clone_chattool_repo(
        chattool_source,
        workspace_path,
        force=force,
        interactive=interactive,
        can_prompt=can_prompt,
    )
    skills_source = _workspace_skills_source(workspace_path)
    _validate_cloned_repo(skills_source)

    logger.info(f"Cloned ChatTool repo dir: {repo_path}")
    logger.info(f"Skills source dir: {skills_source}")

    memory_dir = workspace_path / "Memory"
    logs_dir = memory_dir / "logs"
    retros_dir = memory_dir / "retros"
    skills_dir = workspace_path / "skills"
    scratch_dir = workspace_path / "scratch"
    memory_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    retros_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)
    scratch_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Writing workspace guide files")
    _write_text_file(workspace_path / "AGENTS.md", _render_agents_md(workspace_path, repo_path), force=force)
    _write_text_file(workspace_path / "CHATTOOL.md", _render_chattool_md(workspace_path, repo_path), force=force)
    _write_text_file(workspace_path / "MEMORY.md", _render_memory_md(workspace_path, repo_path), force=force)
    _write_text_file(memory_dir / "README.md", _render_memory_readme(), force=force)
    _write_text_file(memory_dir / "projects.md", _render_memory_projects(), force=force)
    _write_text_file(memory_dir / "decisions.md", _render_memory_decisions(), force=force)
    _write_text_file(logs_dir / "README.md", _render_memory_logs_readme(), force=force)
    _write_text_file(retros_dir / "README.md", _render_memory_retros_readme(), force=force)
    _write_text_file(scratch_dir / "README.md", _render_scratch_readme(), force=force)

    logger.info("Copying workspace skills and creating experience directories")
    copied_skills = _copy_skills(skills_source, skills_dir, force=force)

    logger.info(f"Playground setup completed with {len(copied_skills)} skills")
    click.echo("Playground setup completed.")
    click.echo(f"Workspace: {workspace_path}")
    click.echo(f"ChatTool repo: {repo_path}")
    click.echo(f"Memory summary: {workspace_path / 'MEMORY.md'}")
    click.echo(f"Memory: {memory_dir}")
    click.echo(f"Skills: {skills_dir}")
    click.echo(f"Scratch: {scratch_dir}")
    click.echo(f"Copied skills: {len(copied_skills)}")
    _maybe_setup_github_auth(interactive=interactive, can_prompt=can_prompt)
