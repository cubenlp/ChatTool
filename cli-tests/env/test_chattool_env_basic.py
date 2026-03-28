import os
import pty
import select
import subprocess
import sys
from pathlib import Path

import pytest


pytestmark = pytest.mark.e2e


def _run_chattool_env(
    args: list[str],
    *,
    config_dir: Path,
    extra_env: dict[str, str] | None = None,
    input_text: str | None = None,
):
    env = os.environ.copy()
    env["CHATTOOL_CONFIG_DIR"] = str(config_dir)
    for key in (
        "OPENAI_API_KEY",
        "OPENAI_API_BASE",
        "OPENAI_API_MODEL",
        "FEISHU_APP_ID",
        "FEISHU_APP_SECRET",
        "FEISHU_DEFAULT_RECEIVER_ID",
        "FEISHU_DEFAULT_CHAT_ID",
        "FEISHU_ENCRYPT_KEY",
        "FEISHU_VERIFY_TOKEN",
    ):
        env.pop(key, None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-m", "chattool.client.main", "env", *args],
        text=True,
        input=input_text,
        capture_output=True,
        env=env,
        check=False,
    )


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _run_chattool_env_pty(
    args: list[str],
    *,
    config_dir: Path,
    input_text: str,
    extra_env: dict[str, str] | None = None,
):
    env = os.environ.copy()
    env["CHATTOOL_CONFIG_DIR"] = str(config_dir)
    for key in (
        "OPENAI_API_KEY",
        "OPENAI_API_BASE",
        "OPENAI_API_MODEL",
        "FEISHU_APP_ID",
        "FEISHU_APP_SECRET",
        "FEISHU_DEFAULT_RECEIVER_ID",
        "FEISHU_DEFAULT_CHAT_ID",
        "FEISHU_ENCRYPT_KEY",
        "FEISHU_VERIFY_TOKEN",
    ):
        env.pop(key, None)
    if extra_env:
        env.update(extra_env)

    master_fd, slave_fd = pty.openpty()
    proc = subprocess.Popen(
        [sys.executable, "-m", "chattool.client.main", "env", *args],
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        env=env,
        close_fds=True,
    )
    os.close(slave_fd)
    os.write(master_fd, input_text.encode("utf-8"))

    output = bytearray()
    while True:
        ready, _, _ = select.select([master_fd], [], [], 0.1)
        if master_fd in ready:
            try:
                chunk = os.read(master_fd, 4096)
            except OSError:
                chunk = b""
            if chunk:
                output.extend(chunk)
        if proc.poll() is not None:
            break

    while True:
        try:
            chunk = os.read(master_fd, 4096)
        except OSError:
            break
        if not chunk:
            break
        output.extend(chunk)

    os.close(master_fd)
    return proc.returncode, output.decode("utf-8", errors="replace")


def test_env_cat_masks_sensitive_values(tmp_path: Path):
    config_dir = tmp_path / "config"
    active_path = config_dir / "envs" / "Feishu" / ".env"
    _write_text(
        active_path,
        "\n".join(
            [
                "FEISHU_APP_ID='cli_a94b2cd8e6f89bb6'",
                "FEISHU_APP_SECRET='secret_value'",
                "FEISHU_DEFAULT_RECEIVER_ID='ou_0f9154e16e9114a95e6952bd6ba4ded4'",
                "",
            ]
        ),
    )

    result = _run_chattool_env(["cat", "-t", "feishu"], config_dir=config_dir)
    assert result.returncode == 0, result.stderr
    assert "FEISHU_APP_ID='cli_a94b2cd8e6f89bb6'" in result.stdout
    assert "FEISHU_DEFAULT_RECEIVER_ID='ou_0f9154e16e9114a95e6952bd6ba4ded4'" in result.stdout
    secret_line = next(
        line for line in result.stdout.splitlines() if line.startswith("FEISHU_APP_SECRET=")
    )
    assert "secret_value" not in secret_line
    assert "*" in secret_line

    result = _run_chattool_env(["cat", "-t", "feishu", "--no-mask"], config_dir=config_dir)
    assert result.returncode == 0, result.stderr
    assert "FEISHU_APP_SECRET='secret_value'" in result.stdout


def test_env_list_profiles_by_type(tmp_path: Path):
    config_dir = tmp_path / "config"
    feishu_dir = config_dir / "envs" / "Feishu"
    feishu_dir.mkdir(parents=True, exist_ok=True)
    (feishu_dir / "profile1.env").write_text("", encoding="utf-8")
    (feishu_dir / "profile2.env").write_text("", encoding="utf-8")

    result = _run_chattool_env(["list", "-t", "feishu"], config_dir=config_dir)
    assert result.returncode == 0, result.stderr
    assert "[Feishu]" in result.stdout
    assert "profile1.env" in result.stdout
    assert "profile2.env" in result.stdout


def test_env_save_use_delete_profile(tmp_path: Path):
    config_dir = tmp_path / "config"

    result = _run_chattool_env(["set", "OPENAI_API_KEY=sk-one"], config_dir=config_dir)
    assert result.returncode == 0, result.stderr

    result = _run_chattool_env(["save", "work", "-t", "openai"], config_dir=config_dir)
    assert result.returncode == 0, result.stderr

    active_path = config_dir / "envs" / "OpenAI" / ".env"
    profile_path = config_dir / "envs" / "OpenAI" / "work.env"
    assert active_path.exists()
    assert profile_path.exists()
    assert "OPENAI_API_KEY='sk-one'" in profile_path.read_text(encoding="utf-8")

    result = _run_chattool_env(["set", "OPENAI_API_KEY=sk-two"], config_dir=config_dir)
    assert result.returncode == 0, result.stderr
    assert "OPENAI_API_KEY='sk-two'" in active_path.read_text(encoding="utf-8")

    result = _run_chattool_env(["use", "work", "-t", "openai"], config_dir=config_dir)
    assert result.returncode == 0, result.stderr
    assert "Activated OpenAI profile 'work.env'" in result.stdout
    assert "OPENAI_API_KEY='sk-one'" in active_path.read_text(encoding="utf-8")

    result = _run_chattool_env(["delete", "work", "-t", "openai"], config_dir=config_dir)
    assert result.returncode == 0, result.stderr
    assert "Deleted OpenAI profile 'work.env'" in result.stdout
    assert not profile_path.exists()


def test_env_new_profile_creates_and_activates(tmp_path: Path):
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
    assert active_path.read_text(encoding="utf-8") == profile_path.read_text(encoding="utf-8")
    assert "FEISHU_APP_ID='cli-one'" in profile_path.read_text(encoding="utf-8")
    assert "FEISHU_APP_SECRET='secret-one'" in profile_path.read_text(encoding="utf-8")


def test_env_new_without_name_prompts_and_configures_type(tmp_path: Path):
    config_dir = tmp_path / "config"

    returncode, output = _run_chattool_env_pty(
        ["new", "-t", "openai"],
        config_dir=config_dir,
        input_text="open1\nhttps://api.example/v1\nsk-open\n\n",
    )
    assert returncode == 0, output
    assert "Configuring OpenAI Configuration" in output

    active_path = config_dir / "envs" / "OpenAI" / ".env"
    profile_path = config_dir / "envs" / "OpenAI" / "open1.env"
    assert active_path.exists()
    assert profile_path.exists()

    content = profile_path.read_text(encoding="utf-8")
    assert "OPENAI_API_BASE='https://api.example/v1'" in content
    assert "OPENAI_API_KEY='sk-open'" in content
    assert "OPENAI_API_MODEL='gpt-3.5-turbo'" in content
    assert active_path.read_text(encoding="utf-8") == content


def test_env_init_type_updates_real_typed_env(tmp_path: Path):
    config_dir = tmp_path / "config"

    result = _run_chattool_env(
        ["init", "-i", "-t", "feishu"],
        config_dir=config_dir,
        input_text="cli-new\nsecret-new\n\nou-user\noc-group\nencrypt-key\nverify-token\n",
    )
    assert result.returncode == 0, result.stderr

    active_path = config_dir / "envs" / "Feishu" / ".env"
    content = active_path.read_text(encoding="utf-8")
    assert "FEISHU_APP_ID='cli-new'" in content
    assert "FEISHU_APP_SECRET='secret-new'" in content
    assert "FEISHU_API_BASE='https://open.feishu.cn'" in content
    assert "FEISHU_DEFAULT_RECEIVER_ID='ou-user'" in content
    assert "FEISHU_DEFAULT_CHAT_ID='oc-group'" in content
    assert "FEISHU_ENCRYPT_KEY='encrypt-key'" in content
    assert "FEISHU_VERIFY_TOKEN='verify-token'" in content

    result = _run_chattool_env(["init", "-t", "NonExistent"], config_dir=config_dir)
    assert result.returncode == 0, result.stderr
    assert "No configuration types matched: NonExistent" in result.stdout


def test_env_set_get_unset_real_config(tmp_path: Path):
    config_dir = tmp_path / "config"

    result = _run_chattool_env(["set", "FEISHU_DEFAULT_CHAT_ID=oc_123"], config_dir=config_dir)
    assert result.returncode == 0, result.stderr

    active_path = config_dir / "envs" / "Feishu" / ".env"
    assert "FEISHU_DEFAULT_CHAT_ID='oc_123'" in active_path.read_text(encoding="utf-8")

    result = _run_chattool_env(["get", "FEISHU_DEFAULT_CHAT_ID"], config_dir=config_dir)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "oc_123"

    result = _run_chattool_env(["unset", "FEISHU_DEFAULT_CHAT_ID"], config_dir=config_dir)
    assert result.returncode == 0, result.stderr
    assert "Unset FEISHU_DEFAULT_CHAT_ID" in result.stdout
    assert "FEISHU_DEFAULT_CHAT_ID=''" in active_path.read_text(encoding="utf-8")
