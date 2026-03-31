import os

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
