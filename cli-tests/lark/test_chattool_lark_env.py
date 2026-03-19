import json
from pathlib import Path

import pytest
from click.testing import CliRunner

import chattool.tools.lark.cli as lark_cli


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


class _FakeBot:
    def __init__(self):
        assert lark_cli.FeishuConfig.FEISHU_APP_ID.value == "cli_test_app"
        assert lark_cli.FeishuConfig.FEISHU_APP_SECRET.value == "secret_test_value"

    def get_bot_info(self):
        content = json.dumps(
            {
                "bot": {
                    "app_name": "Demo Bot",
                    "open_id": "ou_test_bot",
                    "activate_status": 2,
                }
            }
        )
        return type(
            "Resp",
            (),
            {
                "code": 0,
                "raw": type("Raw", (), {"content": content})(),
            },
        )()


def _write_feishu_env(env_path: Path) -> None:
    env_path.write_text(
        "\n".join(
            [
                "FEISHU_APP_ID='cli_test_app'",
                "FEISHU_APP_SECRET='secret_test_value'",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_lark_info_supports_env_file(tmp_path, monkeypatch):
    runner = CliRunner()
    env_file = tmp_path / "feishu.env"
    _write_feishu_env(env_file)

    monkeypatch.setattr(lark_cli, "LarkBot", _FakeBot)

    result = runner.invoke(lark_cli.cli, ["info", "-e", str(env_file)])

    assert result.exit_code == 0
    assert "Demo Bot" in result.output
    assert "已激活" in result.output


def test_lark_info_supports_env_profile(tmp_path, monkeypatch):
    runner = CliRunner()
    env_dir = tmp_path / "envs"
    env_dir.mkdir()
    profile = env_dir / "work.env"
    _write_feishu_env(profile)

    monkeypatch.setattr(lark_cli, "CHATTOOL_ENV_DIR", env_dir)
    monkeypatch.setattr(lark_cli, "LarkBot", _FakeBot)

    result = runner.invoke(lark_cli.cli, ["info", "-e", "work"])

    assert result.exit_code == 0
    assert "Demo Bot" in result.output


def test_lark_info_rejects_missing_env(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr(lark_cli, "CHATTOOL_ENV_DIR", Path("/tmp/chattool-missing-envs"))

    result = runner.invoke(lark_cli.cli, ["info", "-e", "missing-profile"])

    assert result.exit_code != 0
    assert "未找到配置文件" in result.output


class _FakeSendBot:
    def send_text(self, receiver, id_type, text):
        assert receiver == "f25gc16d"
        assert id_type == "user_id"
        assert text == "hello"
        return type(
            "Resp",
            (),
            {
                "success": lambda self: True,
                "data": type("Data", (), {"message_id": "om_test_message"})(),
            },
        )()


def test_lark_send_uses_default_receiver_id(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr(lark_cli, "_load_runtime_env", lambda env_ref: None)
    monkeypatch.setattr(lark_cli, "_get_bot", lambda: _FakeSendBot())
    monkeypatch.setattr(
        lark_cli.FeishuConfig,
        "FEISHU_DEFAULT_RECEIVER_ID",
        type("Field", (), {"value": "f25gc16d"})(),
    )

    result = runner.invoke(lark_cli.cli, ["send", "hello"])

    assert result.exit_code == 0
    assert "发送成功" in result.output


def test_lark_send_requires_receiver_when_default_missing(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr(lark_cli, "_load_runtime_env", lambda env_ref: None)
    monkeypatch.setattr(
        lark_cli.FeishuConfig,
        "FEISHU_DEFAULT_RECEIVER_ID",
        type("Field", (), {"value": None})(),
    )

    result = runner.invoke(lark_cli.cli, ["send", "hello"])

    assert result.exit_code == 0
    assert "单参数形式需要先配置 FEISHU_DEFAULT_RECEIVER_ID" in result.output
