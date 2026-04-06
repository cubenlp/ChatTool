from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_LANGUAGE = "zh"
SUPPORTED_LANGUAGES = {"zh", "en"}
EXPERIENCE_LOG_FORMAT = "date_h_min_标题.log"


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


class BaseProfile(WorkspaceProfile):
    pass


PROFILES: dict[str, WorkspaceProfile] = {
    "base": BaseProfile(
        name="base", description="General-purpose human-AI collaboration workspace."
    ),
}


BASE_DIRS = [
    "reports",
    "playgrounds",
    "docs",
    "docs/memory",
    "docs/tools",
    "core",
    "reference",
    "skills",
    "public",
]


def resolve_profile(profile_name: str | None) -> WorkspaceProfile:
    key = (profile_name or "base").strip().lower()
    profile = PROFILES.get(key)
    if profile is None:
        supported = ", ".join(sorted(PROFILES))
        raise ValueError(
            f"Unknown workspace profile: {profile_name}. Supported: {supported}"
        )
    return profile


def coerce_profile_and_workspace(
    profile_name, workspace_dir
) -> tuple[str | None, str | None]:
    if profile_name and workspace_dir is None:
        candidate = str(profile_name).strip()
        if candidate.lower() not in PROFILES:
            return None, candidate
    return profile_name, workspace_dir


def resolve_language(language: str | None) -> str:
    key = (language or DEFAULT_LANGUAGE).strip().lower()
    if key not in SUPPORTED_LANGUAGES:
        supported = ", ".join(sorted(SUPPORTED_LANGUAGES))
        raise ValueError(
            f"Unknown workspace language: {language}. Supported: {supported}"
        )
    return key
