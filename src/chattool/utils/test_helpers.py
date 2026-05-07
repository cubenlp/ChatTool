from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Tuple
from unittest.mock import patch


def create_temp_env_layout(tmp_path: Path, content: str) -> Tuple[Path, Path]:
    env_dir = tmp_path / "envs"
    env_dir.mkdir(parents=True, exist_ok=True)
    env_file = env_dir / ".env"
    env_file.write_text(content)
    return env_dir, env_file


@contextmanager
def patch_chatenv_paths(env_dir: Path, env_file: Path):
    with (
        patch.dict("os.environ", {"CHATARCH_HOME": str(env_dir.parent)}),
        patch("chattool.const.CHATARCH_ENV_FILE", env_file),
    ):
        yield


@contextmanager
def patch_chatenv_registry(registry: Iterable[type]):
    with patch("chattool.config.BaseEnvConfig._registry", list(registry)):
        yield
