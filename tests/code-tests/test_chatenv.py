import pytest
from click.testing import CliRunner

from chatenv.cli import cli
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
    home = tmp_path
    env_dir = home / "envs"
    env_dir.mkdir(parents=True, exist_ok=True)
    env_file = env_dir / ".env"
    
    # Create active typed env and a legacy .env file. Current chatenv commands
    # should prefer envs/<Config>/.env over the legacy file.
    content = "MOCK_KEY='value1'\nSENSITIVE_KEY='secret_value'\nOTHER_KEY='other'"
    active_dir = env_dir / "Mock"
    active_dir.mkdir()
    (active_dir / ".env").write_text(content)
    env_file.write_text("LEGACY_ONLY='legacy'")
    
    BaseEnvConfig._registry = [MockConfig]
    yield env_dir, env_file

def test_cat(runner, mock_env_setup):
    env_dir, env_file = mock_env_setup
    result = runner.invoke(cli, ['--home', str(env_dir.parent), 'cat'])
    assert result.exit_code == 0
    assert "MOCK_KEY='value1'" in result.output
    assert "SENSITIVE_KEY='************'" in result.output

    # Test no-mask
    result = runner.invoke(cli, ['--home', str(env_dir.parent), 'cat', '--no-mask'])
    assert result.exit_code == 0
    assert "SENSITIVE_KEY='secret_value'" in result.output

def test_profiles(runner, mock_env_setup):
    env_dir, env_file = mock_env_setup
    profile_dir = env_dir / "Mock"
    (profile_dir / "profile1.env").touch()
    (profile_dir / "profile2.env").touch()
    
    result = runner.invoke(cli, ['--home', str(env_dir.parent), 'list', '-t', 'Mock'])
    assert result.exit_code == 0
    assert "profile1" in result.output
    assert "profile2" in result.output

def test_save_use_delete(runner, mock_env_setup):
    env_dir, env_file = mock_env_setup
    
    # Save
    result = runner.invoke(cli, ['--home', str(env_dir.parent), 'save', 'test_profile', '-t', 'Mock'])
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
    result = runner.invoke(cli, ['--home', str(env_dir.parent), 'use', 'test_profile', '-t', 'Mock'])
    assert result.exit_code == 0
    assert "Activated Mock profile 'test_profile.env'" in result.output
    assert active_file.read_text() == profile_file.read_text()
    assert "MOCK_KEY='value1'" in active_file.read_text()
    
    # Delete
    result = runner.invoke(cli, ['--home', str(env_dir.parent), 'delete', 'test_profile', '-t', 'Mock', '-y'])
    assert result.exit_code == 0
    assert not profile_file.exists()

def test_init_type(runner, mock_env_setup):
    env_dir, env_file = mock_env_setup

    import chatenv.cli as chatenv_cli

    original_ask_text = chatenv_cli.ask_text
    chatenv_cli.ask_text = (
        lambda message, default="", password=False: "new_secret" if password else "new_mock_val"
    )
    result = runner.invoke(cli, ['--home', str(env_dir.parent), 'init', '-i', '-t', 'Mock'])
    chatenv_cli.ask_text = original_ask_text
    assert result.exit_code == 0
    
    # Verify values updated in file
    content = (env_dir / "Mock" / ".env").read_text()
    # The saved file format depends on BaseEnvConfig.save_env_file template
    # It usually wraps values in single quotes
    assert "MOCK_KEY='new_mock_val'" in content
    assert "SENSITIVE_KEY='new_secret'" in content

def test_init_type_no_match(runner, mock_env_setup):
    env_dir, env_file = mock_env_setup
    result = runner.invoke(cli, ['--home', str(env_dir.parent), 'init', '-I', '-t', 'NonExistent'])
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
