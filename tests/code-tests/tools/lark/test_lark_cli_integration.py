from click.testing import CliRunner

import pytest

import chattool.tools.lark.cli as lark_cli
from chattool.config import FeishuConfig


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def _require_credentials() -> None:
    if not FeishuConfig.FEISHU_APP_ID.value or not FeishuConfig.FEISHU_APP_SECRET.value:
        pytest.skip("需要默认环境中的 FEISHU_APP_ID / FEISHU_APP_SECRET 才能执行真实飞书 CLI 测试")


def _require_default_user() -> str:
    receiver = FeishuConfig.FEISHU_DEFAULT_RECEIVER_ID.value
    if not receiver:
        pytest.skip("需要 FEISHU_DEFAULT_RECEIVER_ID 才能执行默认用户发送测试")
    return receiver


def _require_default_chat() -> str:
    chat_id = FeishuConfig.FEISHU_DEFAULT_CHAT_ID.value
    if not chat_id:
        pytest.skip("需要 FEISHU_DEFAULT_CHAT_ID 才能执行默认群聊发送测试")
    return chat_id


def test_lark_info_cli_real():
    _require_credentials()
    runner = CliRunner()

    result = runner.invoke(lark_cli.cli, ["info"])

    assert result.exit_code == 0
    assert "名称" in result.output
    assert "激活状态" in result.output


def test_lark_send_cli_real():
    _require_credentials()
    receiver = _require_default_user()
    runner = CliRunner()

    result = runner.invoke(
        lark_cli.cli,
        ["send", receiver, "[test] chattool lark cli real integration"],
    )

    assert result.exit_code == 0
    assert "发送成功" in result.output


def test_lark_send_default_chat_cli_real():
    _require_credentials()
    _require_default_chat()
    runner = CliRunner()

    result = runner.invoke(
        lark_cli.cli,
        ["send", "-t", "chat_id", "[test] chattool lark cli default chat"],
    )

    assert result.exit_code == 0
    assert "发送成功" in result.output
