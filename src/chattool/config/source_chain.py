from __future__ import annotations

import os
from pathlib import Path

from chattool.config import BaseEnvConfig


def read_env_file_values(env_file: str | Path | None) -> dict[str, str]:
    if env_file is None:
        return {}
    return BaseEnvConfig._read_env_values(env_file)


def split_config_sources(
    config_cls, env_root: str | Path | None, legacy_env_file: str | Path | None = None
):
    env_root_path = Path(env_root) if env_root is not None else None
    typed_env_values = {}
    if env_root_path is not None:
        typed_env_values = read_env_file_values(
            config_cls.get_active_env_file(env_root_path)
        )
    elif legacy_env_file is not None:
        typed_env_values = read_env_file_values(legacy_env_file)

    system_env_values = {}
    for field in config_cls.get_fields().values():
        value = os.getenv(field.env_key)
        if value is not None:
            system_env_values[field.env_key] = value

    return system_env_values, typed_env_values
