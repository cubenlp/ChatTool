import json

import pytest

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_setup_lark_cli_prefers_existing_config_over_current_env(
    tmp_path, monkeypatch, runner
):
    config_dir = tmp_path / "lark-cli"
    config_dir.mkdir(parents=True)
    (config_dir / "config.json").write_text(
        json.dumps(
            {
                "apps": [
                    {
                        "appId": "existing-app-id",
                        "brand": "lark",
                        "users": [],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    captured = {}

    def fake_init(args, input_text=None):
        captured["args"] = args
        captured["input_text"] = input_text

        class Result:
            returncode = 0
            stdout = ""
            stderr = ""

        return Result()

    monkeypatch.setenv("LARKSUITE_CLI_CONFIG_DIR", str(config_dir))
    monkeypatch.setenv("FEISHU_APP_ID", "env-app-id")
    monkeypatch.setenv("FEISHU_APP_SECRET", "env-app-secret")
    monkeypatch.setenv("FEISHU_API_BASE", "https://open.feishu.cn")
    monkeypatch.setattr(
        "chattool.setup.lark_cli.ensure_nodejs_requirement",
        lambda interactive, can_prompt: None,
    )
    monkeypatch.setattr(
        "chattool.setup.lark_cli.should_install_global_npm_package",
        lambda *args, **kwargs: False,
    )
    monkeypatch.setattr("chattool.setup.lark_cli._run_lark_cli_command", fake_init)

    result = runner.invoke(
        cli, ["setup", "lark-cli", "-I", "--app-secret", "sk-explicit-secret"]
    )

    assert result.exit_code == 0
    assert captured["args"][3] == "existing-app-id"
    assert captured["args"][6] == "lark"
    assert captured["input_text"] == "sk-explicit-secret\n"
