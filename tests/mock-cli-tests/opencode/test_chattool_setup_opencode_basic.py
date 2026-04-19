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
        lambda interactive, can_prompt, log_level="INFO": None,
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


def test_setup_opencode_prefers_existing_config_over_current_env(
    tmp_path, monkeypatch, runner
):
    home_dir = tmp_path / "home"
    config_dir = home_dir / ".config" / "opencode"
    config_dir.mkdir(parents=True)
    (config_dir / "opencode.json").write_text(
        json.dumps(
            {
                "$schema": "https://opencode.ai/config.json",
                "model": "opencode/existing-model",
                "provider": {
                    "opencode": {
                        "options": {
                            "baseURL": "https://existing.example/v1",
                            "apiKey": "sk-existing",
                        },
                        "models": {"existing-model": {"name": "existing-model"}},
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    monkeypatch.setenv("OPENAI_API_BASE", "https://env.example/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
    monkeypatch.setenv("OPENAI_API_MODEL", "env-model")
    monkeypatch.setattr(
        "chattool.setup.opencode.ensure_nodejs_requirement",
        lambda interactive, can_prompt, log_level="INFO": None,
    )
    monkeypatch.setattr(
        "chattool.setup.opencode.should_install_global_npm_package",
        lambda *args, **kwargs: False,
    )

    result = runner.invoke(cli, ["setup", "opencode", "-I"])

    assert result.exit_code == 0
    payload = json.loads((config_dir / "opencode.json").read_text(encoding="utf-8"))
    provider = payload["provider"]["opencode"]
    assert provider["options"]["baseURL"] == "https://existing.example/v1"
    assert provider["options"]["apiKey"] == "sk-existing"
    assert payload["model"] == "opencode/existing-model"


def test_setup_opencode_explicit_args_override_env_ref(tmp_path, monkeypatch, runner):
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
    monkeypatch.setattr("chattool.setup.opencode.CHATTOOL_ENV_DIR", env_dir)
    monkeypatch.setattr("chattool.setup.opencode.CHATTOOL_ENV_FILE", env_file)
    monkeypatch.setattr("chattool.const.CHATTOOL_ENV_DIR", env_dir)
    monkeypatch.setattr("chattool.const.CHATTOOL_ENV_FILE", env_file)
    monkeypatch.setattr(
        "chattool.setup.opencode.ensure_nodejs_requirement",
        lambda interactive, can_prompt, log_level="INFO": None,
    )
    monkeypatch.setattr(
        "chattool.setup.opencode.should_install_global_npm_package",
        lambda *args, **kwargs: False,
    )

    result = runner.invoke(
        cli,
        [
            "setup",
            "opencode",
            "-I",
            "-e",
            "work",
            "--base-url",
            "https://explicit.example/v1",
            "--api-key",
            "sk-explicit",
            "--model",
            "explicit-model",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(
        (home_dir / ".config" / "opencode" / "opencode.json").read_text(
            encoding="utf-8"
        )
    )
    provider = payload["provider"]["opencode"]
    assert provider["options"]["baseURL"] == "https://explicit.example/v1"
    assert provider["options"]["apiKey"] == "sk-explicit"
    assert payload["model"] == "opencode/explicit-model"


def test_setup_opencode_forwards_log_level_to_nodejs_check(
    tmp_path, monkeypatch, runner
):
    home_dir = tmp_path / "home"
    captured = {}

    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)

    def fake_ensure_nodejs_requirement(interactive, can_prompt, log_level):
        captured["log_level"] = log_level

    monkeypatch.setattr(
        "chattool.setup.opencode.ensure_nodejs_requirement",
        fake_ensure_nodejs_requirement,
    )
    monkeypatch.setattr(
        "chattool.setup.opencode.should_install_global_npm_package",
        lambda *args, **kwargs: False,
    )

    result = runner.invoke(
        cli,
        [
            "setup",
            "opencode",
            "-I",
            "--log-level",
            "DEBUG",
            "--base-url",
            "https://explicit.example/v1",
            "--api-key",
            "sk-explicit",
            "--model",
            "explicit-model",
        ],
    )

    assert result.exit_code == 0
    assert captured["log_level"] == "DEBUG"


def test_setup_opencode_adds_auto_loop_plugin(tmp_path, monkeypatch, runner):
    home_dir = tmp_path / "home"
    config_dir = home_dir / ".config" / "opencode"
    config_dir.mkdir(parents=True)
    (config_dir / "opencode.json").write_text(
        json.dumps(
            {
                "$schema": "https://opencode.ai/config.json",
                "model": "opencode/existing-model",
                "provider": {
                    "opencode": {
                        "options": {
                            "baseURL": "https://existing.example/v1",
                            "apiKey": "sk-existing",
                        },
                        "models": {"existing-model": {"name": "existing-model"}},
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    monkeypatch.setattr(
        "chattool.setup.opencode.ensure_nodejs_requirement",
        lambda interactive, can_prompt, log_level="INFO": None,
    )
    monkeypatch.setattr(
        "chattool.setup.opencode.should_install_global_npm_package",
        lambda *args, **kwargs: False,
    )

    result = runner.invoke(
        cli,
        [
            "setup",
            "opencode",
            "-I",
            "--base-url",
            "https://explicit.example/v1",
            "--api-key",
            "sk-explicit",
            "--model",
            "explicit-model",
            "--plugin",
            "auto-loop",
        ],
    )

    assert result.exit_code == 0
    assert "Enabled OpenCode plugin preset: opencode-auto-loop" in result.output
    payload = json.loads((config_dir / "opencode.json").read_text(encoding="utf-8"))
    assert payload["plugin"] == ["opencode-auto-loop"]
    assert payload["model"] == "opencode/explicit-model"


def test_setup_opencode_install_only_can_install_chatloop(tmp_path, monkeypatch, runner):
    home_dir = tmp_path / "home"

    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    monkeypatch.setattr(
        "chattool.setup.opencode.ensure_nodejs_requirement",
        lambda interactive, can_prompt, log_level="INFO": None,
    )
    monkeypatch.setattr(
        "chattool.setup.opencode.should_install_global_npm_package",
        lambda *args, **kwargs: False,
    )

    result = runner.invoke(
        cli,
        ["setup", "opencode", "-I", "--install-only", "--plugin", "chatloop"],
    )

    assert result.exit_code == 0
    config_path = home_dir / ".config" / "opencode" / "opencode.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    plugin_file = (home_dir / ".config" / "opencode" / "plugins" / "chatloop" / "index.ts").resolve()
    assert payload["plugin"] == [f"file://{plugin_file}"]
    assert plugin_file.exists()
    assert (home_dir / ".config" / "opencode" / "command" / "chatloop.md").exists()
    assert (home_dir / ".config" / "opencode" / "command" / "chatloop-status.md").exists()
    assert f"Enabled OpenCode plugin preset: file://{plugin_file}" in result.output


def test_setup_opencode_interactive_can_select_auto_loop_plugin(
    tmp_path, monkeypatch, runner
):
    home_dir = tmp_path / "home"

    monkeypatch.setattr("pathlib.Path.home", lambda: home_dir)
    monkeypatch.setattr(
        "chattool.setup.opencode.ensure_nodejs_requirement",
        lambda interactive, can_prompt, log_level="INFO": None,
    )
    monkeypatch.setattr(
        "chattool.setup.opencode.should_install_global_npm_package",
        lambda *args, **kwargs: False,
    )
    monkeypatch.setattr(
        "chattool.setup.opencode.resolve_interactive_mode",
        lambda interactive, auto_prompt_condition: (True, True, False, True, True),
    )
    monkeypatch.setattr(
        "chattool.setup.opencode.prompt_text_value",
        lambda label, value, fallback=None: value or fallback,
    )
    monkeypatch.setattr(
        "chattool.setup.opencode.prompt_sensitive_value",
        lambda label, value, masker=None: value or "sk-interactive",
    )
    monkeypatch.setattr(
        "chattool.setup.mode_prompt.ask_confirm",
        lambda message, default=True: True,
    )
    monkeypatch.setattr(
        "chattool.setup.opencode.ask_checkbox_with_controls",
        lambda message, choices, default_values=None, instruction=None, select_all_label=None: [
            "auto-loop"
        ],
    )

    result = runner.invoke(cli, ["setup", "opencode"])

    assert result.exit_code == 0
    payload = json.loads(
        (home_dir / ".config" / "opencode" / "opencode.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["plugin"] == ["opencode-auto-loop"]
