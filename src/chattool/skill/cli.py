from __future__ import annotations

import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import click

from chattool.cli_warnings import install_cli_warning_filters
from chattool.utils.tui import (
    BACK_VALUE,
    ask_checkbox_with_controls,
    ask_select,
    create_choice,
    is_interactive_available,
)

install_cli_warning_filters()


@dataclass(frozen=True)
class PlatformSpec:
    name: str
    home_env_vars: tuple[str, ...]
    default_homes: tuple[Path, ...]
    skills_subdir: str
    allow_create_if_missing: bool


def _build_platforms() -> dict[str, PlatformSpec]:
    home = Path.home()
    return {
        "codex": PlatformSpec(
            name="codex",
            home_env_vars=("CODEX_HOME",),
            default_homes=(home / ".codex",),
            skills_subdir="skills",
            allow_create_if_missing=True,
        ),
        "claude": PlatformSpec(
            name="claude",
            home_env_vars=("CLAUDE_HOME",),
            default_homes=(home / ".claude",),
            skills_subdir="skills",
            allow_create_if_missing=False,
        ),
        "opencode": PlatformSpec(
            name="opencode",
            home_env_vars=("OPENCODE_HOME",),
            default_homes=(home / ".config" / "opencode",),
            skills_subdir="skills",
            allow_create_if_missing=True,
        ),
    }


PLATFORMS = _build_platforms()
REQUIRED_FRONTMATTER_KEYS = ("name", "description")
PLATFORM_CHOICES = tuple(sorted(PLATFORMS.keys()))


def _find_repo_skills_dir() -> Path | None:
    current = Path(__file__).resolve()
    for parent in [current, *current.parents]:
        candidate = parent / "skills"
        if candidate.is_dir():
            return candidate
    return None


def _get_skills_source_env() -> str | None:
    env_source = os.getenv("CHATTOOL_SKILLS_DIR")
    if env_source:
        return env_source

    from chattool.config import SkillsConfig

    return SkillsConfig.CHATTOOL_SKILLS_DIR.value or None


def _resolve_source_dir(source: str | None) -> Path | None:
    if source:
        return Path(source).expanduser().resolve()
    env_source = _get_skills_source_env()
    if env_source:
        return Path(env_source).expanduser().resolve()
    return _find_repo_skills_dir()


def _resolve_platform(name: str | None) -> PlatformSpec:
    platform_name = (name or os.getenv("CHATTOOL_SKILL_PLATFORM") or "codex").strip()
    if platform_name not in PLATFORMS:
        supported = ", ".join(sorted(PLATFORMS))
        raise click.UsageError(
            f"Unknown platform: {platform_name}. Supported: {supported}"
        )
    return PLATFORMS[platform_name]


def _resolve_platform_home(spec: PlatformSpec) -> Path | None:
    for env_var in spec.home_env_vars:
        env_value = os.getenv(env_var)
        if env_value:
            return Path(env_value).expanduser().resolve()
    for candidate in spec.default_homes:
        if candidate.exists():
            return candidate.expanduser().resolve()
    if spec.allow_create_if_missing:
        return spec.default_homes[0].expanduser().resolve()
    return None


def _resolve_dest_dir(platform: PlatformSpec, dest: str | None) -> Path:
    if dest:
        return Path(dest).expanduser().resolve()
    home_dir = _resolve_platform_home(platform)
    if not home_dir:
        env_list = ", ".join(platform.home_env_vars)
        click.echo(f"Could not determine {platform.name} home directory.", err=True)
        if env_list:
            click.echo(
                f"Set {env_list} or pass --dest to specify a skills folder.", err=True
            )
        else:
            click.echo("Pass --dest to specify a skills folder.", err=True)
        raise click.Abort()
    return home_dir / platform.skills_subdir


def _list_skill_dirs(source_dir: Path) -> list[str]:
    if not source_dir.exists():
        return []
    skills = []
    for entry in source_dir.iterdir():
        if entry.is_dir() and (entry / "SKILL.md").exists():
            skills.append(entry.name)
    return sorted(skills)


def _extract_frontmatter_values(skill_md: Path) -> tuple[dict[str, str], list[str]]:
    try:
        content = skill_md.read_text(encoding="utf-8")
    except OSError as exc:
        return {}, [f"failed to read file: {exc}"]

    lines = content.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, ["missing YAML frontmatter delimited by ---"]

    closing_index = None
    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing_index = idx
            break

    if closing_index is None:
        return {}, ["missing closing YAML frontmatter delimiter ---"]

    values = {}
    key_pattern = re.compile(r"^([A-Za-z0-9_-]+)\s*:")
    for raw_line in lines[1:closing_index]:
        if not raw_line.strip() or raw_line[:1].isspace():
            continue
        match = key_pattern.match(raw_line)
        if match:
            key = match.group(1)
            value = raw_line.split(":", 1)[1].strip().strip('"').strip("'")
            values[key] = value

    return values, []


def _validate_skill_dir(skill_dir: Path) -> list[str]:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return ["missing SKILL.md"]

    values, errors = _extract_frontmatter_values(skill_md)
    if errors:
        return errors

    missing = [key for key in REQUIRED_FRONTMATTER_KEYS if key not in values]
    if missing:
        return [f"missing required frontmatter keys: {', '.join(missing)}"]

    return []


def _prompt_install_targets(available: list[str]) -> list[str] | str:
    choices = [
        create_choice(title=skill_name, value=skill_name) for skill_name in available
    ]
    selected = ask_checkbox_with_controls(
        "Select skills to install",
        choices=choices,
        default_values=available,
        instruction="(Use arrow keys to move, <space> to toggle, <a> to toggle all, <enter> to confirm)",
        select_all_label="Select all skills",
    )
    if selected == BACK_VALUE:
        return BACK_VALUE
    return list(selected)


def _prompt_platform() -> str:
    choices = [
        create_choice(title="codex", value="codex"),
        create_choice(title="claude", value="claude"),
        create_choice(title="opencode", value="opencode"),
    ]
    selected = ask_select("Select a platform (default: codex):", choices=choices)
    if selected == BACK_VALUE:
        raise click.Abort()
    return str(selected)


def _prompt_overwrite_action(skill_name: str) -> str:
    while True:
        answer = click.prompt(
            f"Skill already exists: {skill_name}. Overwrite? [y/N/a]",
            default="",
            show_default=False,
            prompt_suffix=" ",
            err=True,
        )
        normalized = answer.strip().lower()
        if normalized in {"", "n", "no"}:
            return "skip"
        if normalized in {"y", "yes"}:
            return "overwrite"
        if normalized == "a":
            return "all"
        click.echo("Please enter y, n, or a.", err=True)


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

    source = _resolve_source_dir(source_dir)
    if not source or not source.exists():
        click.echo("Skills source directory not found.", err=True)
        click.echo(
            "Use --source or set CHATTOOL_SKILLS_DIR to point at the skills folder.",
            err=True,
        )
        raise click.Abort()

    available = _list_skill_dirs(source)
    if not available:
        click.echo(f"No skills found in {source}", err=True)
        raise click.Abort()

    if not platform_name:
        env_platform = os.getenv("CHATTOOL_SKILL_PLATFORM")
        if env_platform:
            platform_name = env_platform
        elif is_interactive_available():
            platform_name = _prompt_platform()
        else:
            platform_name = "codex"

    if not name and not install_all:
        if is_interactive_available():
            selected_targets = _prompt_install_targets(available)
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
        errors = _validate_skill_dir(skill_path)
        if errors:
            invalid_targets.append((skill_path / "SKILL.md", errors))

    if invalid_targets:
        click.echo("Invalid skill definitions detected:", err=True)
        for skill_md, errors in invalid_targets:
            for error in errors:
                click.echo(f"  - {skill_md}: {error}", err=True)
        raise click.Abort()

    platform = _resolve_platform(platform_name)
    dest = _resolve_dest_dir(platform, dest_dir)
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
                    action = _prompt_overwrite_action(dest_name)
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
    source = _resolve_source_dir(source_dir)
    if not source or not source.exists():
        click.echo("Skills source directory not found.", err=True)
        click.echo(
            "Use --source or set CHATTOOL_SKILLS_DIR to point at the skills folder.",
            err=True,
        )
        raise click.Abort()

    skills = _list_skill_dirs(source)
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
