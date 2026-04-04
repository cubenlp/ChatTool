import json

import pytest

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_setup_opencode_reuses_openai_profile(tmp_path, monkeypatch, runner):
    home_dir = tmp_path / "home"
    env_dir = tmp_path / "envs"
    env_file = tmp_path / ".env"
    profile_dir = env_dir / "OpenAI"
    profile_dir.mkdir(parents=True)
    (profile_dir / "work.env").write_text(
        "\n".join(
            [
                "OPENAI_API_BASE='https://example.com/v1'",
                "OPENAI_API_KEY='sk-work-key'",
                "OPENAI_API_MODEL='gpt-4.1-mini'",
                "",
            ]
        ),
        encoding="utf-8",
    )
    env_file.write_text("", encoding="utf-8")

    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    monkeypatch.setattr("chattool.setup.opencode.CHATTOOL_ENV_DIR", env_dir)
    monkeypatch.setattr("chattool.setup.opencode.CHATTOOL_ENV_FILE", env_file)
    monkeypatch.setattr("chattool.const.CHATTOOL_ENV_DIR", env_dir)
    monkeypatch.setattr("chattool.const.CHATTOOL_ENV_FILE", env_file)
    monkeypatch.setattr(
        "chattool.setup.opencode.ensure_nodejs_requirement",
        lambda interactive, can_prompt: None,
    )
    monkeypatch.setattr(
        "chattool.setup.opencode.should_install_global_npm_package",
        lambda *args, **kwargs: False,
    )

    result = runner.invoke(cli, ["setup", "opencode", "-I", "-e", "work"])

    assert result.exit_code == 0
    assert "Reused ChatTool OpenAI config: work" in result.output

    config_path = home_dir / ".config" / "opencode" / "opencode.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    provider = payload["provider"]["opencode"]
    assert provider["options"]["baseURL"] == "https://example.com/v1"
    assert provider["options"]["apiKey"] == "sk-work-key"
    assert payload["model"] == "opencode/gpt-4.1-mini"


def test_setup_opencode_prefers_saved_openai_config_over_os_env(
    tmp_path, monkeypatch, runner
):
    home_dir = tmp_path / "home"
    env_dir = tmp_path / "envs"
    env_file = tmp_path / ".env"
    profile_dir = env_dir / "OpenAI"
    profile_dir.mkdir(parents=True)
    (profile_dir / ".env").write_text(
        "\n".join(
            [
                "OPENAI_API_BASE='https://saved.example/v1'",
                "OPENAI_API_KEY='sk-saved-key'",
                "OPENAI_API_MODEL='saved-model'",
                "",
            ]
        ),
        encoding="utf-8",
    )
    env_file.write_text("", encoding="utf-8")

    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    monkeypatch.setattr("chattool.setup.opencode.CHATTOOL_ENV_DIR", env_dir)
    monkeypatch.setattr("chattool.setup.opencode.CHATTOOL_ENV_FILE", env_file)
    monkeypatch.setattr("chattool.const.CHATTOOL_ENV_DIR", env_dir)
    monkeypatch.setattr("chattool.const.CHATTOOL_ENV_FILE", env_file)
    monkeypatch.setattr(
        "chattool.setup.opencode.ensure_nodejs_requirement",
        lambda interactive, can_prompt: None,
    )
    monkeypatch.setattr(
        "chattool.setup.opencode.should_install_global_npm_package",
        lambda *args, **kwargs: False,
    )
    monkeypatch.setenv("OPENAI_API_BASE", "https://os.example/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-os-key")
    monkeypatch.setenv("OPENAI_API_MODEL", "os-model")

    result = runner.invoke(cli, ["setup", "opencode", "-I"])

    assert result.exit_code == 0
    config_path = home_dir / ".config" / "opencode" / "opencode.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    provider = payload["provider"]["opencode"]
    assert provider["options"]["baseURL"] == "https://saved.example/v1"
    assert provider["options"]["apiKey"] == "sk-saved-key"
    assert payload["model"] == "opencode/saved-model"
