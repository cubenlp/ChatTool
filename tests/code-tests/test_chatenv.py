import pytest
import os
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from pathlib import Path
from chattool.config.cli import cli
from chattool.config import BaseEnvConfig, EnvField

# Mock Config Class for testing
class MockConfig(BaseEnvConfig):
    _title = "Mock"
    mock_key = EnvField("MOCK_KEY", default="default_mock", desc="Mock key description")
    sensitive_key = EnvField("SENSITIVE_KEY", default="secret", desc="Sensitive key", is_sensitive=True)

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def mock_env_setup(tmp_path):
    env_dir = tmp_path / "envs"
    env_dir.mkdir()
    env_file = tmp_path / ".env"
    
    # Create active typed env and a legacy .env file. Current chatenv commands
    # should prefer envs/<Config>/.env over the legacy file.
    content = "MOCK_KEY='value1'\nSENSITIVE_KEY='secret_value'\nOTHER_KEY='other'"
    active_dir = env_dir / "Mock"
    active_dir.mkdir()
    (active_dir / ".env").write_text(content)
    env_file.write_text("LEGACY_ONLY='legacy'")
    
    # We need to patch where CHATARCH_ENV_DIR and CHATARCH_ENV_FILE are used in chatenv.py
    # Since they are imported as names, we must patch chatenv module attributes if possible,
    # or rely on them being module variables.
    # In chatenv.py: from chattool.const import CHATARCH_ENV_FILE, CHATARCH_ENV_DIR
    # So we patch chatenv.CHATARCH_ENV_DIR and chatenv.CHATARCH_ENV_FILE
    
    with patch("chattool.config.cli.CHATARCH_ENV_DIR", env_dir), \
         patch("chattool.config.cli.CHATARCH_ENV_FILE", env_file), \
         patch("chattool.config.BaseEnvConfig._registry", [MockConfig]):
        yield env_dir, env_file

def test_cat(runner, mock_env_setup):
    env_dir, env_file = mock_env_setup
    result = runner.invoke(cli, ['cat'])
    assert result.exit_code == 0
    # Output should contain masked sensitive key
    assert "MOCK_KEY='value1'" in result.output
    # Masking check: SENSITIVE_KEY='secret_value' -> length 12 -> 2 + * + 2
    # secret_value -> se********ue
    # But wait, my masking logic in chatenv.py handles quotes.
    # value is 'secret_value' (including quotes?)
    # In chatenv.py: key, value = line.split('=', 1)
    # value includes quotes if present in file.
    # The file content I wrote has quotes: SENSITIVE_KEY='secret_value'
    # So value is "'secret_value'".
    # My logic: 
    # if (val_part.startswith("'")...): quote = "'"; raw_val = "secret_value"
    # masked raw_val -> se********ue
    # output -> SENSITIVE_KEY='se********ue'
    assert "SENSITIVE_KEY='se********ue'" in result.output

    # Test no-mask
    result = runner.invoke(cli, ['cat', '--no-mask'])
    assert result.exit_code == 0
    assert "SENSITIVE_KEY='secret_value'" in result.output

def test_profiles(runner, mock_env_setup):
    env_dir, env_file = mock_env_setup
    profile_dir = env_dir / "Mock"
    (profile_dir / "profile1.env").touch()
    (profile_dir / "profile2.env").touch()
    
    result = runner.invoke(cli, ['list', '-t', 'Mock'])
    assert result.exit_code == 0
    assert "profile1" in result.output
    assert "profile2" in result.output

def test_save_use_delete(runner, mock_env_setup):
    env_dir, env_file = mock_env_setup
    
    # Save
    result = runner.invoke(cli, ['save', 'test_profile', '-t', 'Mock'])
    assert result.exit_code == 0
    profile_file = env_dir / "Mock" / "test_profile.env"
    active_file = env_dir / "Mock" / ".env"
    assert profile_file.exists()
    profile_content = profile_file.read_text()
    assert "MOCK_KEY='value1'" in profile_content
    assert "SENSITIVE_KEY='secret_value'" in profile_content
    
    # Modify current active typed .env
    active_file.write_text("MOCK_KEY='modified'")
    
    # Use
    result = runner.invoke(cli, ['use', 'test_profile', '-t', 'Mock'])
    assert result.exit_code == 0
    assert "Activated Mock profile 'test_profile.env'" in result.output
    assert active_file.read_text() == profile_file.read_text()
    assert "MOCK_KEY='value1'" in active_file.read_text()
    
    # Delete
    result = runner.invoke(cli, ['delete', 'test_profile', '-t', 'Mock'])
    assert result.exit_code == 0
    assert not profile_file.exists()

def test_init_type(runner, mock_env_setup):
    env_dir, env_file = mock_env_setup
    
    # Inputs: "new_mock_val", "new_secret"
    # We use input argument for prompts
    result = runner.invoke(cli, ['init', '-i', '-t', 'Mock'], input="new_mock_val\nnew_secret\n")
    assert result.exit_code == 0
    
    # Verify values updated in file
    content = (env_dir / "Mock" / ".env").read_text()
    # The saved file format depends on BaseEnvConfig.save_env_file template
    # It usually wraps values in single quotes
    assert "MOCK_KEY='new_mock_val'" in content
    assert "SENSITIVE_KEY='new_secret'" in content

def test_init_type_no_match(runner, mock_env_setup):
    result = runner.invoke(cli, ['init', '-t', 'NonExistent'])
    assert result.exit_code == 0
    assert "No configuration types matched" in result.output

# def test_set_get_unset(runner, mock_env_setup):
#     env_dir, env_file = mock_env_setup
    
#     # Set
#     result = runner.invoke(cli, ['set', 'MOCK_KEY=set_value'])
#     assert result.exit_code == 0
#     assert "Set MOCK_KEY=set_value" in result.output
#     # The set command updates memory and calls save_env_file
#     assert "MOCK_KEY='set_value'" in env_file.read_text()
    
#     # Get
#     # Note: get uses BaseEnvConfig.get_all_values().
#     # This reads from memory (class fields).
#     # Since 'set' updated class fields, 'get' should work.
#     result = runner.invoke(cli, ['get', 'MOCK_KEY'])
#     assert result.exit_code == 0
#     assert "set_value" in result.output
    
#     # Unset
#     result = runner.invoke(cli, ['unset', 'MOCK_KEY'])
#     assert result.exit_code == 0
#     assert "Unset MOCK_KEY" in result.output
#     assert "MOCK_KEY=''" in env_file.read_text()
