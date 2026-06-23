from __future__ import annotations

from pathlib import Path
import subprocess

import click

from chattool.interaction import (
    BACK_VALUE,
    ask_checkbox_with_controls,
    ask_confirm,
    create_choice,
)


CHATBLOG_REPO_URL = "https://github.com/ChatArch/ChatBlog.git"
CHATMEMORY_REPO_URL = "https://github.com/ChatArch/ChatMemory.git"
DEFAULT_MEMORY_SKILL_GROUPS = ("chatarch", "common", "agents")
LOCAL_SKILL_GROUP_README = """# Local Skills

Use this directory for machine-specific, workspace-specific, or private skills that should not be shared through ChatMemory.

Shared skills should live in one of the linked ChatMemory groups: `chatarch`, `common`, or `agents`.
"""


def _run_git(
    args: list[str], workdir: Path | None = None
) -> subprocess.CompletedProcess[str]:
    command = ["git"]
    if workdir is not None:
        command.extend(["-C", str(workdir)])
    command.extend(args)
    return subprocess.run(command, capture_output=True, text=True)


def _clone_or_update_repo(
    repo_source: str, repo_dir: Path, interactive, can_prompt: bool
) -> str:
    if not repo_dir.exists():
        result = _run_git(["clone", repo_source, str(repo_dir)])
        if result.returncode != 0:
            raise click.ClickException(
                result.stderr.strip() or f"Failed to clone {repo_source}"
            )
        return "cloned"

    if not (repo_dir / ".git").exists():
        raise click.ClickException(f"Existing path is not a git repo: {repo_dir}")

    dirty = _run_git(["status", "--porcelain"], workdir=repo_dir)
    if dirty.returncode == 0 and dirty.stdout.strip():
        if interactive is not False and can_prompt:
            keep = ask_confirm(
                f"{repo_dir} has local changes. Skip update?", default=True
            )
            if keep == BACK_VALUE:
                raise click.Abort()
            if keep:
                return "skipped"
        else:
            return "skipped"

    fetch = _run_git(["fetch", "--prune", repo_source], workdir=repo_dir)
    if fetch.returncode != 0:
        raise click.ClickException(
            fetch.stderr.strip() or f"Failed to fetch {repo_source}"
        )
    merge = _run_git(["merge", "--ff-only", "FETCH_HEAD"], workdir=repo_dir)
    if merge.returncode != 0:
        raise click.ClickException(
            merge.stderr.strip() or f"Failed to fast-forward {repo_dir}"
        )
    return "updated"


def _ensure_symlink(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        target.unlink()
    elif target.exists():
        raise click.ClickException(
            f"Refusing to replace existing non-symlink path: {target}"
        )
    target.symlink_to(source)


def _ensure_local_skill_group(workspace_dir: Path) -> Path:
    local_dir = workspace_dir / "skills" / "local"
    if local_dir.is_symlink():
        raise click.ClickException(
            f"Refusing to use symlink for local-only skill group: {local_dir}"
        )
    local_dir.mkdir(parents=True, exist_ok=True)
    readme = local_dir / "README.md"
    if not readme.exists():
        readme.write_text(LOCAL_SKILL_GROUP_README, encoding="utf-8")
    return local_dir


def apply_chatblog_option(
    workspace_dir: Path,
    source: str,
    interactive,
    can_prompt: bool,
) -> dict:
    repo_dir = workspace_dir / "core" / "ChatBlog"
    repo_action = _clone_or_update_repo(source, repo_dir, interactive, can_prompt)
    posts_dir = repo_dir / "source" / "_posts"
    if not posts_dir.exists():
        return {
            "name": "chatblog",
            "repo_dir": repo_dir,
            "repo_action": repo_action,
            "public_link": None,
            "posts_dir": posts_dir,
            "posts_linked": False,
        }
    public_link = workspace_dir / "public" / "chatblog"
    _ensure_symlink(posts_dir, public_link)
    return {
        "name": "chatblog",
        "repo_dir": repo_dir,
        "repo_action": repo_action,
        "public_link": public_link,
        "posts_dir": posts_dir,
        "posts_linked": True,
    }


def apply_memory_option(
    workspace_dir: Path,
    source: str,
    interactive,
    can_prompt: bool,
) -> dict:
    repo_dir = workspace_dir / "core" / "ChatMemory"
    repo_action = _clone_or_update_repo(source, repo_dir, interactive, can_prompt)
    skills_root = repo_dir / "Skills"
    if not skills_root.exists():
        raise click.ClickException(
            f"ChatMemory repo does not contain Skills/: {skills_root}"
        )

    linked_groups: list[str] = []
    skipped_groups: list[str] = []
    for group in DEFAULT_MEMORY_SKILL_GROUPS:
        group_source = skills_root / group
        if not group_source.exists():
            skipped_groups.append(group)
            continue
        _ensure_symlink(group_source, workspace_dir / "skills" / group)
        linked_groups.append(group)

    local_group = _ensure_local_skill_group(workspace_dir)

    return {
        "name": "memory",
        "repo_dir": repo_dir,
        "repo_action": repo_action,
        "linked_groups": linked_groups,
        "skipped_groups": skipped_groups,
        "local_group": local_group,
    }


def prompt_optional_modules(language: str) -> dict[str, dict]:
    results = {
        "chatblog": {
            "enabled": False,
            "source": CHATBLOG_REPO_URL,
        },
        "memory": {
            "enabled": False,
            "source": CHATMEMORY_REPO_URL,
        },
    }

    enable_extras = ask_confirm(
        "Configure extra workspace modules?"
        if language == "en"
        else "是否配置额外的 workspace 模块？",
        default=False,
    )
    if enable_extras == BACK_VALUE:
        raise click.Abort()
    if not enable_extras:
        return results

    selected = ask_checkbox_with_controls(
        "Select extra workspace modules"
        if language == "en"
        else "选择额外的 workspace 模块",
        choices=[
            create_choice("ChatBlog -> core/ChatBlog + public/chatblog", "chatblog"),
            create_choice("ChatMemory -> core/ChatMemory + skills/chatarch, skills/common, skills/agents + local", "memory"),
        ],
        default_values=[],
        instruction="",
        select_all_label="Select all" if language == "en" else "全选",
    )
    if selected == BACK_VALUE:
        raise click.Abort()

    for key in selected:
        if key in results:
            results[key]["enabled"] = True
    return results
