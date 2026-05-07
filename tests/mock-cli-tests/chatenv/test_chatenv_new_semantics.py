from chattool.config import BaseEnvConfig, EnvField
from chatenv.cli import cli


class MockConfig(BaseEnvConfig):
    _title = "Mock Configuration"
    _aliases = ["mock"]
    _storage_dir = "Mock"

    MOCK_KEY = EnvField("MOCK_KEY", default="default_mock")


def test_new_only_creates_profile_without_touching_active(tmp_path, monkeypatch, runner):
    home = tmp_path
    env_dir = home / "envs"
    env_file = env_dir / ".env"
    active_dir = env_dir / "Mock"
    active_dir.mkdir(parents=True)
    active_file = active_dir / ".env"
    active_file.write_text("MOCK_KEY='active_value'\n", encoding="utf-8")
    env_dir.mkdir(parents=True, exist_ok=True)
    env_file.write_text("", encoding="utf-8")
    monkeypatch.setenv("CHATARCH_HOME", str(home))

    monkeypatch.setattr("chattool.config.BaseEnvConfig._registry", [MockConfig])

    result = runner.invoke(cli, ["new", "snapshot", "-t", "mock"])

    assert result.exit_code == 0
    assert "Created Mock profile 'snapshot.env'" in result.output

    profile_file = active_dir / "snapshot.env"
    assert profile_file.exists()
    assert "MOCK_KEY='active_value'" in profile_file.read_text(encoding="utf-8")
    assert active_file.read_text(encoding="utf-8") == "MOCK_KEY='active_value'\n"
