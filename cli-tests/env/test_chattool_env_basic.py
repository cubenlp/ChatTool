from pathlib import Path

import pytest
from click.testing import CliRunner

from chattool.config import BaseEnvConfig, EnvField
from chattool.client.main import cli
from chattool.utils import create_temp_env_layout, patch_chatenv_registry


pytestmark = pytest.mark.e2e


class MockConfig(BaseEnvConfig):
    _title = "MockConfig"
    mock_key = EnvField("MOCK_KEY", default="default_mock", desc="Mock key description")
    sensitive_key = EnvField(
        "SENSITIVE_KEY", default="secret", desc="Sensitive key", is_sensitive=True
    )
    default_only = EnvField("DEFAULT_ONLY", default="default_from_field", desc="Defaulted field")


def _set_env_dirs(monkeypatch, tmp_path: Path) -> tuple[Path, Path]:
    config_dir = tmp_path / "config"
    cache_dir = tmp_path / "cache"
    monkeypatch.setenv("CHATTOOL_CONFIG_DIR", str(config_dir))
    monkeypatch.setenv("CHATTOOL_CACHE_DIR", str(cache_dir))
    return config_dir, cache_dir


def _patch_env_paths(monkeypatch, config_dir: Path, cache_dir: Path) -> None:
    env_dir = config_dir / "envs"
    env_file = config_dir / ".env"

    import chattool.const as const
    import chattool.config.cli as env_cli

    monkeypatch.setattr(const, "CHATTOOL_CONFIG_DIR", config_dir, raising=False)
    monkeypatch.setattr(const, "CHATTOOL_ENV_DIR", env_dir, raising=False)
    monkeypatch.setattr(const, "CHATTOOL_ENV_FILE", env_file, raising=False)
    monkeypatch.setattr(const, "CHATTOOL_CACHE_DIR", cache_dir, raising=False)

    monkeypatch.setattr(env_cli, "CHATTOOL_ENV_DIR", env_dir, raising=False)
    monkeypatch.setattr(env_cli, "CHATTOOL_ENV_FILE", env_file, raising=False)


def test_env_cat_masks_sensitive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runner = CliRunner()
    config_dir, cache_dir = _set_env_dirs(monkeypatch, tmp_path)
    _patch_env_paths(monkeypatch, config_dir, cache_dir)
    env_dir, env_file = create_temp_env_layout(
        config_dir,
        "MOCK_KEY='value1'\nSENSITIVE_KEY='secret_value'\nOTHER_KEY='other'",
    )
    BaseEnvConfig.load_all(env_file)

    with patch_chatenv_registry([MockConfig]):
        result = runner.invoke(cli, ["env", "cat"])
        assert result.exit_code == 0
        assert "MOCK_KEY='value1'" in result.output
        assert "SENSITIVE_KEY='se********ue'" in result.output

        result = runner.invoke(cli, ["env", "cat", "--no-mask"])
        assert result.exit_code == 0
        assert "SENSITIVE_KEY='secret_value'" in result.output


def test_env_cat_type_renders_effective_values_from_env_and_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runner = CliRunner()
    config_dir, cache_dir = _set_env_dirs(monkeypatch, tmp_path)
    _patch_env_paths(monkeypatch, config_dir, cache_dir)
    _, env_file = create_temp_env_layout(
        config_dir,
        "MOCK_KEY='value1'\n",
    )
    monkeypatch.setenv("SENSITIVE_KEY", "secret_from_os_env")
    BaseEnvConfig.load_all(env_file)

    with patch_chatenv_registry([MockConfig]):
        result = runner.invoke(cli, ["env", "cat", "-t", "MockConfig"])
        assert result.exit_code == 0
        assert "MOCK_KEY='value1'" in result.output
        assert "SENSITIVE_KEY='secr**********_env'" in result.output
        assert "DEFAULT_ONLY='default_from_field'" in result.output

        result = runner.invoke(cli, ["env", "cat", "-t", "MockConfig", "--no-mask"])
        assert result.exit_code == 0
        assert "SENSITIVE_KEY='secret_from_os_env'" in result.output


def test_env_list_profiles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runner = CliRunner()
    config_dir, cache_dir = _set_env_dirs(monkeypatch, tmp_path)
    _patch_env_paths(monkeypatch, config_dir, cache_dir)
    env_dir, env_file = create_temp_env_layout(
        config_dir,
        "MOCK_KEY='value1'\nSENSITIVE_KEY='secret_value'\nOTHER_KEY='other'",
    )
    BaseEnvConfig.load_all(env_file)
    (env_dir / "profile1.env").touch()
    (env_dir / "profile2.env").touch()

    with patch_chatenv_registry([MockConfig]):
        result = runner.invoke(cli, ["env", "list"])
        assert result.exit_code == 0
        assert "profile1" in result.output
        assert "profile2" in result.output


def test_env_save_use_delete_profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runner = CliRunner()
    config_dir, cache_dir = _set_env_dirs(monkeypatch, tmp_path)
    _patch_env_paths(monkeypatch, config_dir, cache_dir)
    env_dir, env_file = create_temp_env_layout(
        config_dir,
        "MOCK_KEY='value1'\nSENSITIVE_KEY='secret_value'\nOTHER_KEY='other'",
    )
    BaseEnvConfig.load_all(env_file)

    with patch_chatenv_registry([MockConfig]):
        result = runner.invoke(cli, ["env", "save", "test_profile"])
        assert result.exit_code == 0
        assert (env_dir / "test_profile.env").exists()
        assert (env_dir / "test_profile.env").read_text() == env_file.read_text()

        env_file.write_text("MOCK_KEY='modified'")

        result = runner.invoke(cli, ["env", "use", "test_profile"])
        assert result.exit_code == 0
        assert "Activated profile 'test_profile'" in result.output
        assert env_file.read_text() == (env_dir / "test_profile.env").read_text()
        assert "MOCK_KEY='value1'" in env_file.read_text()

        result = runner.invoke(cli, ["env", "delete", "test_profile"])
        assert result.exit_code == 0
        assert not (env_dir / "test_profile.env").exists()


def test_env_init_type(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runner = CliRunner()
    config_dir, cache_dir = _set_env_dirs(monkeypatch, tmp_path)
    _patch_env_paths(monkeypatch, config_dir, cache_dir)
    env_dir, env_file = create_temp_env_layout(
        config_dir,
        "MOCK_KEY='value1'\nSENSITIVE_KEY='secret_value'\nOTHER_KEY='other'",
    )
    BaseEnvConfig.load_all(env_file)

    with patch_chatenv_registry([MockConfig]):
        result = runner.invoke(
            cli,
            ["env", "init", "-i", "-t", "MockConfig"],
            input="new_mock_val\nnew_secret\n\n",
        )
        assert result.exit_code == 0
        content = env_file.read_text()
        assert "MOCK_KEY='new_mock_val'" in content
        assert "SENSITIVE_KEY='new_secret'" in content

        result = runner.invoke(cli, ["env", "init", "-t", "NonExistent"])
        assert result.exit_code == 0
        assert "No configuration types matched" in result.output


def test_env_set_get_unset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runner = CliRunner()
    config_dir, cache_dir = _set_env_dirs(monkeypatch, tmp_path)
    _patch_env_paths(monkeypatch, config_dir, cache_dir)
    _, env_file = create_temp_env_layout(
        config_dir,
        "MOCK_KEY='value1'\n",
    )
    BaseEnvConfig.load_all(env_file)

    with patch_chatenv_registry([MockConfig]):
        result = runner.invoke(cli, ["env", "set", "mock_key=bar"])
        assert result.exit_code == 0
        assert "MOCK_KEY='bar'" in env_file.read_text()

        result = runner.invoke(cli, ["env", "get", "mock_key"])
        assert result.exit_code == 0
        assert "bar" in result.output

        result = runner.invoke(cli, ["env", "unset", "mock_key"])
        assert result.exit_code == 0
        assert "MOCK_KEY=''" in env_file.read_text()
