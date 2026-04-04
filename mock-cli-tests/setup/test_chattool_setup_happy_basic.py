from pathlib import Path

import pytest

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_setup_happy_prints_bootstrap_summary(monkeypatch, runner):
    monkeypatch.setattr(
        "chattool.setup.happy.ensure_nodejs_requirement",
        lambda interactive, can_prompt: None,
    )
    monkeypatch.setattr(
        "chattool.setup.happy.should_install_global_npm_package",
        lambda *args, **kwargs: False,
    )

    result = runner.invoke(
        cli,
        [
            "setup",
            "happy",
            "-I",
            "--base-url",
            "https://relay.example/v1",
            "--api-key",
            "sk-happy",
        ],
    )

    assert result.exit_code == 0
    assert "Happy coder bootstrap summary:" in result.output
    assert "chattool setup codex -e happy" in result.output
    assert "chattool setup opencode -e happy" in result.output
    assert "happy auth login" in result.output


def test_setup_happy_write_env_saves_profiles(tmp_path, monkeypatch, runner):
    env_root = tmp_path / "envs"
    monkeypatch.setattr("chattool.setup.happy.CHATTOOL_ENV_DIR", env_root)
    monkeypatch.setattr(
        "chattool.setup.happy.ensure_nodejs_requirement",
        lambda interactive, can_prompt: None,
    )
    monkeypatch.setattr(
        "chattool.setup.happy.should_install_global_npm_package",
        lambda *args, **kwargs: False,
    )

    result = runner.invoke(
        cli,
        [
            "setup",
            "happy",
            "-I",
            "--write-env",
            "--base-url",
            "https://relay.example/v1",
            "--api-key",
            "sk-happy",
            "--model",
            "gpt-5.4",
            "--server-url",
            "https://happy.example/api",
            "--webapp-url",
            "https://happy.example/app",
        ],
    )

    assert result.exit_code == 0
    openai_profile = Path(env_root) / "OpenAI" / "happy.env"
    happy_profile = Path(env_root) / "Happy" / "happy.env"
    assert openai_profile.exists()
    assert happy_profile.exists()
    assert "OPENAI_API_BASE='https://relay.example/v1'" in openai_profile.read_text(
        encoding="utf-8"
    )
    assert "OPENAI_API_KEY='sk-happy'" in openai_profile.read_text(encoding="utf-8")
    assert "HAPPY_SERVER_URL='https://happy.example/api'" in happy_profile.read_text(
        encoding="utf-8"
    )
    assert "HAPPY_WEBAPP_URL='https://happy.example/app'" in happy_profile.read_text(
        encoding="utf-8"
    )
