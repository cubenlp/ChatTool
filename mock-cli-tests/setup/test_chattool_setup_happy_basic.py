from pathlib import Path

import pytest

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_setup_happy_prints_install_summary(monkeypatch, runner):
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
        ],
    )

    assert result.exit_code == 0
    assert "Happy setup summary:" in result.output
    assert "Official mode: keep Happy's own hosted defaults" in result.output
    assert "happy auth login" in result.output


def test_setup_happy_saves_active_happy_config(tmp_path, monkeypatch, runner):
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
            "--server-url",
            "https://happy.example/api",
            "--webapp-url",
            "https://happy.example/app",
        ],
    )

    assert result.exit_code == 0
    happy_profile = Path(env_root) / "Happy" / ".env"
    assert happy_profile.exists()
    assert "HAPPY_SERVER_URL='https://happy.example/api'" in happy_profile.read_text(
        encoding="utf-8"
    )
    assert "HAPPY_WEBAPP_URL='https://happy.example/app'" in happy_profile.read_text(
        encoding="utf-8"
    )
