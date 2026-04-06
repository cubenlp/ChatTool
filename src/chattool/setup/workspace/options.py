from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess

import click

from chattool.interaction import (
    BACK_VALUE,
    ask_checkbox_with_controls,
    ask_confirm,
    create_choice,
)
from chattool.utils.pathing import write_text_file


CHATTOOL_REPO_URL = "https://github.com/cubenlp/ChatTool.git"
REXBLOG_REPO_URL = "https://github.com/RexWzh/RexBlog"


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


def _copy_skill_tree(src: Path, dst: Path) -> list[str]:
    copied = []
    dst.mkdir(parents=True, exist_ok=True)
    for skill_dir in sorted(src.iterdir()):
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
            continue
        target_dir = dst / skill_dir.name
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(skill_dir, target_dir)
        copied.append(skill_dir.name)
    return copied


def apply_chattool_option(
    workspace_dir: Path, source: str, interactive, can_prompt: bool
) -> dict:
    repo_dir = workspace_dir / "core" / "ChatTool"
    repo_action = _clone_or_update_repo(source, repo_dir, interactive, can_prompt)
    skills_source = repo_dir / "skills"
    if not skills_source.exists():
        raise click.ClickException(
            f"ChatTool repo does not contain skills/: {skills_source}"
        )
    copied_skills = _copy_skill_tree(skills_source, workspace_dir / "skills")
    return {
        "name": "chattool",
        "repo_dir": repo_dir,
        "repo_action": repo_action,
        "copied_skills": copied_skills,
    }


def _ensure_symlink(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        if target.is_symlink() or target.is_file():
            target.unlink()
        else:
            shutil.rmtree(target)
    target.symlink_to(source)


def apply_rexblog_option(
    workspace_dir: Path, source: str, interactive, can_prompt: bool
) -> dict:
    repo_dir = workspace_dir / "core" / "RexBlog"
    repo_action = _clone_or_update_repo(source, repo_dir, interactive, can_prompt)
    posts_dir = repo_dir / "source" / "_posts"
    if not posts_dir.exists():
        raise click.ClickException(
            f"RexBlog repo does not contain source/_posts: {posts_dir}"
        )
    public_link = workspace_dir / "public" / "hexo_blog"
    _ensure_symlink(posts_dir, public_link)
    return {
        "name": "rexblog",
        "repo_dir": repo_dir,
        "repo_action": repo_action,
        "public_link": public_link,
    }


def prompt_optional_modules(language: str) -> dict[str, dict]:
    results = {
        "chattool": {"enabled": False, "source": CHATTOOL_REPO_URL},
        "rexblog": {"enabled": False, "source": REXBLOG_REPO_URL},
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
            create_choice("ChatTool -> core/ChatTool + ./skills", "chattool"),
            create_choice("RexBlog -> core/RexBlog + public/hexo_blog", "rexblog"),
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
