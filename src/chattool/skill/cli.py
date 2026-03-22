import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import click


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
        "claude-code": PlatformSpec(
            name="claude-code",
            home_env_vars=("CLAUDE_CODE_HOME", "CLAUDE_HOME"),
            default_homes=(home / ".claude-code", home / ".claude"),
            skills_subdir="skills",
            allow_create_if_missing=False,
        ),
    }


PLATFORMS = _build_platforms()
REQUIRED_FRONTMATTER_KEYS = ("name", "description", "version")
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


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
        raise click.UsageError(f"Unknown platform: {platform_name}. Supported: {supported}")
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
            click.echo(f"Set {env_list} or pass --dest to specify a skills folder.", err=True)
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

    version = values.get("version", "")
    if not SEMVER_PATTERN.match(version):
        return [f"invalid version '{version}', expected semantic version like 0.1.0"]

    return []


@click.group(name="skill")
def skill_cli():
    """Manage ChatTool skills."""
    pass


@skill_cli.command(name="install")
@click.argument("name", required=False)
@click.option("-a", "--all", "install_all", is_flag=True, help="Install all skills from source directory.")
@click.option(
    "-p",
    "--platform",
    "platform_name",
    type=click.Choice(sorted(PLATFORMS.keys())),
    default=os.getenv("CHATTOOL_SKILL_PLATFORM", "codex"),
    show_default=True,
    help="Target platform for skill installation.",
)
@click.option("-s", "--source", "source_dir", type=click.Path(file_okay=False, dir_okay=True), help="Source skills directory.")
@click.option("-d", "--dest", "dest_dir", type=click.Path(file_okay=False, dir_okay=True), help="Destination skills directory.")
@click.option("--prefix", is_flag=True, help="Prefix installed skill names with chattool-.")
@click.option("-f", "--force", is_flag=True, help="Overwrite existing skills.")
def install_skill(name, install_all, platform_name, source_dir, dest_dir, prefix, force):
    if not name and not install_all:
        click.echo("Missing skill name. Use --all to install all skills.", err=True)
        raise click.Abort()
    if name and install_all:
        click.echo("Cannot use a skill name together with --all.", err=True)
        raise click.Abort()

    source = _resolve_source_dir(source_dir)
    if not source or not source.exists():
        click.echo("Skills source directory not found.", err=True)
        click.echo("Use --source or set CHATTOOL_SKILLS_DIR to point at the skills folder.", err=True)
        raise click.Abort()

    available = _list_skill_dirs(source)
    if not available:
        click.echo(f"No skills found in {source}", err=True)
        raise click.Abort()

    if install_all:
        targets = available
    else:
        if name not in available:
            click.echo(f"Skill not found: {name}", err=True)
            click.echo("Available skills:", err=True)
            for item in available:
                click.echo(f"  - {item}", err=True)
            raise click.Abort()
        targets = [name]

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
    for skill_name in targets:
        src_path = source / skill_name
        dest_name = f"chattool-{skill_name}" if prefix else skill_name
        dest_path = dest / dest_name
        if dest_path.exists():
            if not force:
                if sys.stdin.isatty() and sys.stdout.isatty():
                    if not click.confirm(f"Skill already exists: {dest_name}. Overwrite?", default=False):
                        skipped.append(dest_name)
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
@click.option("--source", "source_dir", type=click.Path(file_okay=False, dir_okay=True), help="Source skills directory.")
def list_skills(source_dir):
    source = _resolve_source_dir(source_dir)
    if not source or not source.exists():
        click.echo("Skills source directory not found.", err=True)
        click.echo("Use --source or set CHATTOOL_SKILLS_DIR to point at the skills folder.", err=True)
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
