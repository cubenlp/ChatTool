from __future__ import annotations

import os
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


def build_platforms() -> dict[str, PlatformSpec]:
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


PLATFORMS = build_platforms()
PLATFORM_CHOICES = tuple(sorted(PLATFORMS.keys()))


def find_repo_skills_dir() -> Path | None:
    current = Path(__file__).resolve()
    for parent in [current, *current.parents]:
        candidate = parent / "skills"
        if candidate.is_dir():
            return candidate
    return None


def get_skills_source_env() -> str | None:
    env_source = os.getenv("CHATTOOL_SKILLS_DIR")
    if env_source:
        return env_source

    from chattool.config import SkillsConfig

    return SkillsConfig.CHATTOOL_SKILLS_DIR.value or None


def resolve_source_dir(source: str | None) -> Path | None:
    if source:
        return Path(source).expanduser().resolve()
    env_source = get_skills_source_env()
    if env_source:
        return Path(env_source).expanduser().resolve()
    return find_repo_skills_dir()


def resolve_platform(name: str | None) -> PlatformSpec:
    platform_name = (name or os.getenv("CHATTOOL_SKILL_PLATFORM") or "codex").strip()
    if platform_name not in PLATFORMS:
        supported = ", ".join(sorted(PLATFORMS))
        raise click.UsageError(
            f"Unknown platform: {platform_name}. Supported: {supported}"
        )
    return PLATFORMS[platform_name]


def resolve_platform_home(spec: PlatformSpec) -> Path | None:
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


def resolve_dest_dir(platform: PlatformSpec, dest: str | None) -> Path:
    if dest:
        return Path(dest).expanduser().resolve()
    home_dir = resolve_platform_home(platform)
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
