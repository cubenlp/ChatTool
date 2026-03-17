from pathlib import Path

from click.testing import CliRunner

from chattool.config import BaseEnvConfig, EnvField
from chattool.config.cli import cli
from chattool.utils import (
    create_temp_env_layout,
    patch_chatenv_paths,
    patch_chatenv_registry,
)


class MockConfig(BaseEnvConfig):
    _title = "MockConfig"
    mock_key = EnvField("MOCK_KEY", default="default_mock", desc="Mock key description")
    sensitive_key = EnvField(
        "SENSITIVE_KEY", default="secret", desc="Sensitive key", is_sensitive=True
    )


def test_chatenv_cat_masks_sensitive(tmp_path: Path):
    runner = CliRunner()
    env_dir, env_file = create_temp_env_layout(
        tmp_path, "MOCK_KEY='value1'\nSENSITIVE_KEY='secret_value'\nOTHER_KEY='other'"
    )

    with patch_chatenv_paths(env_dir, env_file), patch_chatenv_registry([MockConfig]):
        result = runner.invoke(cli, ["cat"])
        assert result.exit_code == 0
        assert "MOCK_KEY='value1'" in result.output
        assert "SENSITIVE_KEY='se********ue'" in result.output

        result = runner.invoke(cli, ["cat", "--no-mask"])
        assert result.exit_code == 0
        assert "SENSITIVE_KEY='secret_value'" in result.output


def test_chatenv_list_profiles(tmp_path: Path):
    runner = CliRunner()
    env_dir, env_file = create_temp_env_layout(
        tmp_path, "MOCK_KEY='value1'\nSENSITIVE_KEY='secret_value'\nOTHER_KEY='other'"
    )
    (env_dir / "profile1.env").touch()
    (env_dir / "profile2.env").touch()

    with patch_chatenv_paths(env_dir, env_file), patch_chatenv_registry([MockConfig]):
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "profile1" in result.output
        assert "profile2" in result.output


def test_chatenv_save_use_delete_profile(tmp_path: Path):
    runner = CliRunner()
    env_dir, env_file = create_temp_env_layout(
        tmp_path, "MOCK_KEY='value1'\nSENSITIVE_KEY='secret_value'\nOTHER_KEY='other'"
    )

    with patch_chatenv_paths(env_dir, env_file), patch_chatenv_registry([MockConfig]):
        result = runner.invoke(cli, ["save", "test_profile"])
        assert result.exit_code == 0
        assert (env_dir / "test_profile.env").exists()
        assert (env_dir / "test_profile.env").read_text() == env_file.read_text()

        env_file.write_text("MOCK_KEY='modified'")

        result = runner.invoke(cli, ["use", "test_profile"])
        assert result.exit_code == 0
        assert "Activated profile 'test_profile'" in result.output
        assert env_file.read_text() == (env_dir / "test_profile.env").read_text()
        assert "MOCK_KEY='value1'" in env_file.read_text()

        result = runner.invoke(cli, ["delete", "test_profile"])
        assert result.exit_code == 0
        assert not (env_dir / "test_profile.env").exists()


def test_chatenv_init_type(tmp_path: Path):
    runner = CliRunner()
    env_dir, env_file = create_temp_env_layout(
        tmp_path, "MOCK_KEY='value1'\nSENSITIVE_KEY='secret_value'\nOTHER_KEY='other'"
    )

    with patch_chatenv_paths(env_dir, env_file), patch_chatenv_registry([MockConfig]):
        result = runner.invoke(
            cli, ["init", "-i", "-t", "MockConfig"], input="new_mock_val\nnew_secret\n"
        )
        assert result.exit_code == 0
        content = env_file.read_text()
        assert "MOCK_KEY='new_mock_val'" in content
        assert "SENSITIVE_KEY='new_secret'" in content

        result = runner.invoke(cli, ["init", "-t", "NonExistent"])
        assert result.exit_code == 0
        assert "No configuration types matched" in result.output
