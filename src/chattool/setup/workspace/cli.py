from __future__ import annotations

from pathlib import Path

import click

from chattool.interaction import (
    BACK_VALUE,
    abort_if_force_without_tty,
    ask_select,
    ask_text,
    create_choice,
    resolve_interactive_mode,
)
from chattool.utils.pathing import display_path, resolve_workspace_dir, write_text_file

from .core import (
    BASE_DIRS,
    PROFILES,
    coerce_profile_and_workspace,
    resolve_language,
    resolve_profile,
)
from . import options as workspace_options
from .render import base_file_map


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


def _plan_workspace(
    workspace_dir: Path, language: str, enabled_options: list[str], profile
) -> tuple[list[Path], dict[Path, str]]:
    dir_paths = [workspace_dir / rel for rel in BASE_DIRS]
    dir_paths.extend(workspace_dir / rel for rel in profile.extra_dirs())
    file_map = base_file_map(workspace_dir, profile, language, enabled_options)
    planned_files = {workspace_dir / rel: content for rel, content in file_map.items()}
    return dir_paths, planned_files


def _render_dry_run(
    workspace_dir: Path,
    profile_name: str,
    language: str,
    enabled_options: list[str],
    dir_paths: list[Path],
    file_map: dict[Path, str],
) -> None:
    click.echo(
        "Workspace setup dry run." if language == "en" else "Workspace 初始化预演。"
    )
    click.echo(f"Workspace: {workspace_dir}")
    click.echo(f"Profile: {profile_name}")
    click.echo(f"Language: {language}")
    click.echo(
        f"Enabled options: {', '.join(enabled_options) if enabled_options else 'none'}"
    )
    click.echo("Directories:" if language == "en" else "将创建目录：")
    for path in dir_paths:
        click.echo(f"  - {display_path(path, workspace_dir)}")
    click.echo("Files:" if language == "en" else "将写入文件：")
    for path in file_map:
        click.echo(f"  - {display_path(path, workspace_dir)}")


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
    profile_name, workspace_dir = coerce_profile_and_workspace(
        profile_name, workspace_dir
    )
    language = resolve_language(language)
    workspace_default = resolve_workspace_dir(workspace_dir=workspace_dir)
    needs_prompt = profile_name is None or workspace_dir is None
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

    abort_if_force_without_tty(force_interactive, can_prompt, usage)

    option_settings = {
        "chattool": {
            "enabled": bool(with_chattool),
            "source": chattool_source or workspace_options.CHATTOOL_REPO_URL,
        },
        "rexblog": {"enabled": False, "source": workspace_options.REXBLOG_REPO_URL},
    }

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
        option_settings = workspace_options.prompt_optional_modules(language)

    profile = resolve_profile(profile_name)
    workspace_path = resolve_workspace_dir(workspace_dir=workspace_dir)
    enabled_options = [
        name for name, item in option_settings.items() if item["enabled"]
    ]
    dir_paths, file_map = _plan_workspace(
        workspace_path, language, enabled_options, profile
    )

    if dry_run:
        _render_dry_run(
            workspace_path, profile.name, language, enabled_options, dir_paths, file_map
        )
        return

    workspace_path.mkdir(parents=True, exist_ok=True)
    for path in dir_paths:
        path.mkdir(parents=True, exist_ok=True)

    for path, content in file_map.items():
        write_text_file(path, content, force=force)

    applied = []
    if option_settings["chattool"]["enabled"]:
        applied.append(
            workspace_options.apply_chattool_option(
                workspace_path,
                option_settings["chattool"]["source"],
                interactive,
                can_prompt,
            )
        )
    if option_settings["rexblog"]["enabled"]:
        applied.append(
            workspace_options.apply_rexblog_option(
                workspace_path,
                option_settings["rexblog"]["source"],
                interactive,
                can_prompt,
            )
        )

    click.echo(
        "Workspace setup completed." if language == "en" else "Workspace 初始化完成。"
    )
    click.echo(f"Workspace: {workspace_path}")
    click.echo(f"Profile: {profile.name}")
    click.echo(f"Language: {language}")
    click.echo(
        f"Enabled options: {', '.join(enabled_options) if enabled_options else 'none'}"
    )
    for item in applied:
        if item["name"] == "chattool":
            click.echo(f"ChatTool repo: {item['repo_dir']}")
            click.echo(f"Repo action: {item['repo_action']}")
            click.echo(f"Skills: {workspace_path / 'skills'}")
            click.echo(f"Copied skills: {len(item['copied_skills'])}")
        if item["name"] == "rexblog":
            click.echo(f"RexBlog repo: {item['repo_dir']}")
            click.echo(f"Repo action: {item['repo_action']}")
            click.echo(f"Public link: {item['public_link']}")
