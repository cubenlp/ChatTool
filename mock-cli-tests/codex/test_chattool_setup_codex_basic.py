import json

import pytest

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_setup_codex_prefers_existing_config_over_current_env(
    tmp_path, monkeypatch, runner
):
    home_dir = tmp_path / "home"
    codex_dir = home_dir / ".codex"
    codex_dir.mkdir(parents=True)
    (codex_dir / "auth.json").write_text(
        json.dumps({"OPENAI_API_KEY": "sk-existing"}),
        encoding="utf-8",
    )
    (codex_dir / "config.toml").write_text(
        "\n".join(
            [
                'model_provider = "crs"',
                'model = "existing-model"',
                'preferred_auth_method = "apikey"',
                "",
                "[model_providers.crs]",
                'base_url = "https://existing.example/v1"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    monkeypatch.setenv("OPENAI_API_BASE", "https://env.example/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
    monkeypatch.setenv("OPENAI_API_MODEL", "env-model")
    monkeypatch.setattr(
        "chattool.setup.codex.ensure_nodejs_requirement",
        lambda interactive, can_prompt: None,
    )
    monkeypatch.setattr(
        "chattool.setup.codex.should_install_global_npm_package",
        lambda *args, **kwargs: False,
    )

    result = runner.invoke(cli, ["setup", "codex", "-I"])

    assert result.exit_code == 0
    auth_payload = json.loads((codex_dir / "auth.json").read_text(encoding="utf-8"))
    config_text = (codex_dir / "config.toml").read_text(encoding="utf-8")
    assert auth_payload["OPENAI_API_KEY"] == "sk-existing"
    assert 'base_url = "https://existing.example/v1"' in config_text
    assert 'model = "existing-model"' in config_text


def test_setup_codex_explicit_args_override_env_ref(tmp_path, monkeypatch, runner):
    home_dir = tmp_path / "home"
    env_dir = tmp_path / "envs"
    env_file = tmp_path / ".env"
    profile_dir = env_dir / "OpenAI"
    profile_dir.mkdir(parents=True)
    (profile_dir / "work.env").write_text(
        "\n".join(
            [
                "OPENAI_API_BASE='https://profile.example/v1'",
                "OPENAI_API_KEY='sk-profile'",
                "OPENAI_API_MODEL='profile-model'",
                "",
            ]
        ),
        encoding="utf-8",
    )
    env_file.write_text("", encoding="utf-8")

    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    monkeypatch.setattr("chattool.setup.codex.CHATTOOL_ENV_DIR", env_dir)
    monkeypatch.setattr("chattool.setup.codex.CHATTOOL_ENV_FILE", env_file)
    monkeypatch.setattr("chattool.const.CHATTOOL_ENV_DIR", env_dir)
    monkeypatch.setattr("chattool.const.CHATTOOL_ENV_FILE", env_file)
    monkeypatch.setattr(
        "chattool.setup.codex.ensure_nodejs_requirement",
        lambda interactive, can_prompt: None,
    )
    monkeypatch.setattr(
        "chattool.setup.codex.should_install_global_npm_package",
        lambda *args, **kwargs: False,
    )

    result = runner.invoke(
        cli,
        [
            "setup",
            "codex",
            "-I",
            "-e",
            "work",
            "--pam",
            "sk-explicit",
            "--base-url",
            "https://explicit.example/v1",
            "--model",
            "explicit-model",
        ],
    )

    assert result.exit_code == 0
    auth_payload = json.loads(
        (home_dir / ".codex" / "auth.json").read_text(encoding="utf-8")
    )
    config_text = (home_dir / ".codex" / "config.toml").read_text(encoding="utf-8")
    assert auth_payload["OPENAI_API_KEY"] == "sk-explicit"
    assert 'base_url = "https://explicit.example/v1"' in config_text
    assert 'model = "explicit-model"' in config_text
