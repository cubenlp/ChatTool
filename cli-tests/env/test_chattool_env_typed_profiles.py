import os
import subprocess
import sys
from pathlib import Path


def _run_chattool_env(args: list[str], *, config_dir: Path, extra_env: dict[str, str] | None = None):
    env = os.environ.copy()
    env["CHATTOOL_CONFIG_DIR"] = str(config_dir)
    env.pop("OPENAI_API_KEY", None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-m", "chattool.client.main", "env", *args],
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def test_env_typed_profile_roundtrip(tmp_path: Path):
    config_dir = tmp_path / "config"

    result = _run_chattool_env(["set", "OPENAI_API_KEY=sk-one"], config_dir=config_dir)
    assert result.returncode == 0, result.stderr

    result = _run_chattool_env(["save", "work", "-t", "openai"], config_dir=config_dir)
    assert result.returncode == 0, result.stderr

    result = _run_chattool_env(["set", "OPENAI_API_KEY=sk-two"], config_dir=config_dir)
    assert result.returncode == 0, result.stderr

    result = _run_chattool_env(["use", "work", "-t", "openai"], config_dir=config_dir)
    assert result.returncode == 0, result.stderr

    active_path = config_dir / "envs" / "OpenAI" / ".env"
    profile_path = config_dir / "envs" / "OpenAI" / "work.env"
    assert active_path.exists()
    assert profile_path.exists()
    assert "OPENAI_API_KEY='sk-one'" in active_path.read_text(encoding="utf-8")
    assert active_path.read_text(encoding="utf-8") == profile_path.read_text(encoding="utf-8")


def test_env_os_environment_overrides_typed_env_file(tmp_path: Path):
    config_dir = tmp_path / "config"

    result = _run_chattool_env(["set", "OPENAI_API_KEY=from_env_file"], config_dir=config_dir)
    assert result.returncode == 0, result.stderr

    result = _run_chattool_env(
        ["cat", "-t", "openai", "--no-mask"],
        config_dir=config_dir,
        extra_env={"OPENAI_API_KEY": "from_os"},
    )
    assert result.returncode == 0, result.stderr
    assert "OPENAI_API_KEY='from_os'" in result.stdout


def test_env_list_profiles_by_type(tmp_path: Path):
    config_dir = tmp_path / "config"
    openai_dir = config_dir / "envs" / "OpenAI"
    openai_dir.mkdir(parents=True, exist_ok=True)
    (openai_dir / "profile1.env").write_text("", encoding="utf-8")
    (openai_dir / "profile2.env").write_text("", encoding="utf-8")

    result = _run_chattool_env(["list", "-t", "openai"], config_dir=config_dir)
    assert result.returncode == 0, result.stderr
    assert "[OpenAI]" in result.stdout
    assert "profile1.env" in result.stdout
    assert "profile2.env" in result.stdout
