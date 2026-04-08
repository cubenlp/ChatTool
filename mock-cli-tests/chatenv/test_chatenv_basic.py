import os
import shutil

from click.testing import CliRunner

from chattool.config import BaseEnvConfig, EnvField
from chattool.config.cli import cli


class MockConfig(BaseEnvConfig):
    _title = "Mock Configuration"
    _aliases = ["mock"]
    _storage_dir = "Mock"

    MOCK_KEY = EnvField("MOCK_KEY", default="default_mock")


def test_cat_prefers_typed_env_over_shell_env(tmp_path, monkeypatch):
    env_dir = tmp_path / "envs"
    env_file = tmp_path / ".env"
    active_dir = env_dir / "Mock"
    active_dir.mkdir(parents=True)
    active_file = active_dir / ".env"
    active_file.write_text("MOCK_KEY='from_file'\n", encoding="utf-8")
    env_file.write_text("", encoding="utf-8")

    monkeypatch.setattr("chattool.config.cli.CHATTOOL_ENV_DIR", env_dir)
    monkeypatch.setattr("chattool.config.cli.CHATTOOL_ENV_FILE", env_file)
    monkeypatch.setattr("chattool.const.CHATTOOL_ENV_DIR", env_dir)
    monkeypatch.setattr("chattool.const.CHATTOOL_ENV_FILE", env_file)
    monkeypatch.setattr("chattool.config.BaseEnvConfig._registry", [MockConfig])
    monkeypatch.setenv("MOCK_KEY", "from_env")

    result = CliRunner().invoke(cli, ["cat", "-t", "mock"])

    assert result.exit_code == 0
    assert "MOCK_KEY='from_file'" in result.output
    assert "from_env" not in result.output


def test_profile_and_key_commands_prompt_when_args_missing(tmp_path, monkeypatch):
    env_dir = tmp_path / "envs"
    env_file = tmp_path / ".env"
    env_file.write_text("", encoding="utf-8")
    monkeypatch.setattr("chattool.config.cli.CHATTOOL_ENV_DIR", env_dir)
    monkeypatch.setattr("chattool.config.cli.CHATTOOL_ENV_FILE", env_file)
    monkeypatch.setattr("chattool.const.CHATTOOL_ENV_DIR", env_dir)
    monkeypatch.setattr("chattool.const.CHATTOOL_ENV_FILE", env_file)
    monkeypatch.setattr("chattool.config.BaseEnvConfig._registry", [MockConfig])
    monkeypatch.setattr(
        "chattool.interaction.policy.is_interactive_available", lambda: True
    )

    answers = {
        "profile name": "demo",
        "key": "MOCK_KEY",
        "KEY=VALUE": "MOCK_KEY=updated",
    }
    monkeypatch.setattr(
        "chattool.interaction.command_schema.ask_text",
        lambda message, default="", password=False, style=None: answers[message],
    )
    monkeypatch.setattr(
        "chattool.config.cli.ask_confirm", lambda message, default=False: True
    )

    active_dir = env_dir / "Mock"
    active_dir.mkdir(parents=True)
    active_file = active_dir / ".env"
    active_file.write_text("MOCK_KEY='from_file'\n", encoding="utf-8")
    profile_file = active_dir / "demo.env"
    profile_file.write_text("MOCK_KEY='from_profile'\n", encoding="utf-8")

    runner = CliRunner()
    save_result = runner.invoke(cli, ["save", "-t", "mock"], catch_exceptions=False)
    get_result = runner.invoke(cli, ["get"], catch_exceptions=False)
    set_result = runner.invoke(cli, ["set"], catch_exceptions=False)
    use_result = runner.invoke(cli, ["use", "-t", "mock"], catch_exceptions=False)
    unset_result = runner.invoke(cli, ["unset"], catch_exceptions=False)
    delete_result = runner.invoke(cli, ["delete", "-t", "mock"], catch_exceptions=False)

    assert save_result.exit_code == 0
    assert get_result.exit_code == 0
    assert set_result.exit_code == 0
    assert use_result.exit_code == 0
    assert unset_result.exit_code == 0
    assert delete_result.exit_code == 0


def test_chatenv_get_errors_with_no_interaction():
    result = CliRunner().invoke(cli, ["get", "-I"])

    assert result.exit_code != 0
    assert "Missing required value: key" in result.output
