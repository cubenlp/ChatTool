"""SkillsConfig env schema."""

from .base import BaseEnvConfig, EnvField


class SkillsConfig(BaseEnvConfig):
    _title = "ChatTool Skills Configuration"
    _aliases = ["skills", "skill", "chattool-skills"]
    _storage_dir = "Skills"

    CHATTOOL_SKILLS_DIR = EnvField(
        "CHATTOOL_SKILLS_DIR",
        desc="Default ChatTool skills source directory.",
    )


__all__ = ["SkillsConfig"]
