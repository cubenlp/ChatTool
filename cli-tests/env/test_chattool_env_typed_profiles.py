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


def _run_python(code: str, *, config_dir: Path, extra_env: dict[str, str] | None = None):
    env = os.environ.copy()
    env["CHATTOOL_CONFIG_DIR"] = str(config_dir)
    env.pop("FEISHU_APP_ID", None)
    env.pop("FEISHU_APP_SECRET", None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-c", code],
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


def test_env_new_typed_profile_creates_and_activates(tmp_path: Path):
    config_dir = tmp_path / "config"

    result = _run_chattool_env(["set", "FEISHU_APP_ID=cli-one"], config_dir=config_dir)
    assert result.returncode == 0, result.stderr
    result = _run_chattool_env(["set", "FEISHU_APP_SECRET=secret-one"], config_dir=config_dir)
    assert result.returncode == 0, result.stderr

    result = _run_chattool_env(["new", "mini", "-t", "feishu"], config_dir=config_dir)
    assert result.returncode == 0, result.stderr
    assert "Created and activated Feishu profile 'mini.env'" in result.stdout

    active_path = config_dir / "envs" / "Feishu" / ".env"
    profile_path = config_dir / "envs" / "Feishu" / "mini.env"
    assert active_path.exists()
    assert profile_path.exists()
    assert "FEISHU_APP_ID='cli-one'" in profile_path.read_text(encoding="utf-8")
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


def test_lark_explicit_env_ref_overrides_os_environment(tmp_path: Path):
    config_dir = tmp_path / "config"
    feishu_dir = config_dir / "envs" / "Feishu"
    feishu_dir.mkdir(parents=True, exist_ok=True)
    (feishu_dir / ".env").write_text(
        "FEISHU_APP_ID='from_builtin'\nFEISHU_APP_SECRET='builtin_secret'\n",
        encoding="utf-8",
    )
    (feishu_dir / "work.env").write_text(
        "FEISHU_APP_ID='from_explicit'\nFEISHU_APP_SECRET='explicit_secret'\n",
        encoding="utf-8",
    )

    with_env_ref = _run_python(
        "\n".join(
            [
                "from chattool.tools.lark.cli import _load_runtime_env",
                "from chattool.config import FeishuConfig",
                "_load_runtime_env('work')",
                "print(FeishuConfig.FEISHU_APP_ID.value)",
            ]
        ),
        config_dir=config_dir,
        extra_env={
            "FEISHU_APP_ID": "from_os",
            "FEISHU_APP_SECRET": "os_secret",
        },
    )
    assert with_env_ref.returncode == 0, with_env_ref.stderr
    assert with_env_ref.stdout.strip() == "from_explicit"

    without_env_ref = _run_python(
        "from chattool.config import FeishuConfig; print(FeishuConfig.FEISHU_APP_ID.value)",
        config_dir=config_dir,
        extra_env={
            "FEISHU_APP_ID": "from_os",
            "FEISHU_APP_SECRET": "os_secret",
        },
    )
    assert without_env_ref.returncode == 0, without_env_ref.stderr
    assert without_env_ref.stdout.strip() == "from_os"
