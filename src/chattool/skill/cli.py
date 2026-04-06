from __future__ import annotations

import os
import shutil
import sys

import click

from chattool.interaction import (
    BACK_VALUE,
    install_cli_warning_filters,
    is_interactive_available,
)
from chattool.skill.interaction import (
    prompt_install_targets,
    prompt_overwrite_action,
    prompt_platform,
)
from chattool.skill.platforms import (
    PLATFORM_CHOICES,
    resolve_dest_dir,
    resolve_platform,
    resolve_source_dir,
)
from chattool.skill.validation import list_skill_dirs, validate_skill_dir

install_cli_warning_filters()


@click.group(name="skill")
def skill_cli():
    """Manage ChatTool skills."""
    pass


@skill_cli.command(name="install")
@click.argument("name", required=False)
@click.option(
    "-a",
    "--all",
    "install_all",
    is_flag=True,
    help="Install all skills from source directory.",
)
@click.option(
    "-p",
    "--platform",
    "platform_name",
    type=click.Choice(PLATFORM_CHOICES),
    default=None,
    help="Target platform for skill installation (codex / claude / opencode). Omit in TTY to choose interactively; non-interactive mode defaults to codex.",
)
@click.option(
    "-s",
    "--source",
    "source_dir",
    type=click.Path(file_okay=False, dir_okay=True),
    help="Source skills directory.",
)
@click.option(
    "-d",
    "--dest",
    "dest_dir",
    type=click.Path(file_okay=False, dir_okay=True),
    help="Destination skills directory.",
)
@click.option(
    "--prefix", is_flag=True, help="Prefix installed skill names with chattool-."
)
@click.option("-f", "--force", is_flag=True, help="Overwrite existing skills.")
def install_skill(
    name, install_all, platform_name, source_dir, dest_dir, prefix, force
):
    if name and install_all:
        click.echo("Cannot use a skill name together with --all.", err=True)
        raise click.Abort()

    source = resolve_source_dir(source_dir)
    if not source or not source.exists():
        click.echo("Skills source directory not found.", err=True)
        click.echo(
            "Use --source or set CHATTOOL_SKILLS_DIR to point at the skills folder.",
            err=True,
        )
        raise click.Abort()

    available = list_skill_dirs(source)
    if not available:
        click.echo(f"No skills found in {source}", err=True)
        raise click.Abort()

    if not platform_name:
        env_platform = os.getenv("CHATTOOL_SKILL_PLATFORM")
        if env_platform:
            platform_name = env_platform
        elif is_interactive_available():
            platform_name = prompt_platform()
        else:
            platform_name = "codex"

    if not name and not install_all:
        if is_interactive_available():
            selected_targets = prompt_install_targets(available)
            if selected_targets == BACK_VALUE:
                raise click.Abort()
            targets = list(selected_targets)
        else:
            click.echo("Missing skill name. Use --all to install all skills.", err=True)
            raise click.Abort()
    elif install_all:
        targets = available
    else:
        if name not in available:
            click.echo(f"Skill not found: {name}", err=True)
            click.echo("Available skills:", err=True)
            for item in available:
                click.echo(f"  - {item}", err=True)
            raise click.Abort()
        targets = [name]

    if not targets:
        click.echo("No skills selected.", err=True)
        raise click.Abort()

    invalid_targets = []
    for skill_name in targets:
        skill_path = source / skill_name
        errors = validate_skill_dir(skill_path)
        if errors:
            invalid_targets.append((skill_path / "SKILL.md", errors))

    if invalid_targets:
        click.echo("Invalid skill definitions detected:", err=True)
        for skill_md, errors in invalid_targets:
            for error in errors:
                click.echo(f"  - {skill_md}: {error}", err=True)
        raise click.Abort()

    platform = resolve_platform(platform_name)
    dest = resolve_dest_dir(platform, dest_dir)
    dest.mkdir(parents=True, exist_ok=True)

    installed = []
    skipped = []
    overwrite_all = force
    for skill_name in targets:
        src_path = source / skill_name
        dest_name = f"chattool-{skill_name}" if prefix else skill_name
        dest_path = dest / dest_name
        if dest_path.exists():
            if not overwrite_all:
                if is_interactive_available():
                    action = prompt_overwrite_action(dest_name)
                    if action == "skip":
                        skipped.append(dest_name)
                        continue
                    if action == "all":
                        overwrite_all = True
                        shutil.rmtree(dest_path)
                        shutil.copytree(src_path, dest_path)
                        installed.append(dest_name)
                        continue
                else:
                    skipped.append(dest_name)
                    continue
            shutil.rmtree(dest_path)
        shutil.copytree(src_path, dest_path)
        installed.append(dest_name)

    if installed:
        click.echo(f"Installed skills to {dest} ({platform.name}):")
        for item in installed:
            click.echo(f"  - {item}")
    if skipped:
        click.echo("Skipped existing skills (use --force to overwrite):")
        for item in skipped:
            click.echo(f"  - {item}")


@skill_cli.command(name="list")
@click.option(
    "--source",
    "source_dir",
    type=click.Path(file_okay=False, dir_okay=True),
    help="Source skills directory.",
)
def list_skills(source_dir):
    source = resolve_source_dir(source_dir)
    if not source or not source.exists():
        click.echo("Skills source directory not found.", err=True)
        click.echo(
            "Use --source or set CHATTOOL_SKILLS_DIR to point at the skills folder.",
            err=True,
        )
        raise click.Abort()

    skills = list_skill_dirs(source)
    if not skills:
        click.echo(f"No skills found in {source}")
        return

    click.echo(f"Available skills in {source}:")
    for item in skills:
        click.echo(f"  - {item}")


def main():
    skill_cli()


if __name__ == "__main__":
    main()
