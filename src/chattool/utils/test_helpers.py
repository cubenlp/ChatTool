from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Tuple
from unittest.mock import patch


def create_temp_env_layout(tmp_path: Path, content: str) -> Tuple[Path, Path]:
    env_dir = tmp_path / "envs"
    env_dir.mkdir()
    env_file = tmp_path / ".env"
    env_file.write_text(content)
    return env_dir, env_file


@contextmanager
def patch_chatenv_paths(env_dir: Path, env_file: Path):
    with (
        patch("chattool.config.cli.CHATTOOL_ENV_DIR", env_dir),
        patch("chattool.config.cli.CHATTOOL_ENV_FILE", env_file),
    ):
        yield


@contextmanager
def patch_chatenv_registry(registry: Iterable[type]):
    with patch("chattool.config.BaseEnvConfig._registry", list(registry)):
        yield
