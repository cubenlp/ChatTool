from click.testing import CliRunner
import time

import pytest

import chattool.tools.lark.cli as lark_cli
from chattool.config import FeishuConfig


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def _require_credentials() -> None:
    if not FeishuConfig.FEISHU_APP_ID.value or not FeishuConfig.FEISHU_APP_SECRET.value:
        pytest.skip("需要默认环境中的 FEISHU_APP_ID / FEISHU_APP_SECRET 才能执行真实飞书 CLI 测试")


def _require_test_user() -> str:
    receiver = FeishuConfig.FEISHU_TEST_USER_ID.value or FeishuConfig.FEISHU_DEFAULT_RECEIVER_ID.value
    if not receiver:
        pytest.skip("需要 FEISHU_TEST_USER_ID 或 FEISHU_DEFAULT_RECEIVER_ID 才能执行真实发送类 CLI 测试")
    return receiver


def test_lark_info_cli_real():
    _require_credentials()
    runner = CliRunner()

    result = runner.invoke(lark_cli.cli, ["info"])

    assert result.exit_code == 0
    assert "名称" in result.output
    assert "激活状态" in result.output


def test_lark_scopes_cli_real():
    _require_credentials()
    runner = CliRunner()

    result = runner.invoke(lark_cli.cli, ["scopes", "-f", "im"])

    assert result.exit_code == 0
    assert "请求失败" not in result.output
    assert "没有匹配的权限" not in result.output


def test_lark_send_cli_real():
    _require_credentials()
    receiver = _require_test_user()
    runner = CliRunner()

    result = runner.invoke(
        lark_cli.cli,
        ["send", receiver, "[test] chattool lark cli real integration"],
    )

    assert result.exit_code == 0
    assert "发送成功" in result.output


def test_lark_notify_doc_cli_real(tmp_path):
    _require_credentials()
    _require_test_user()
    runner = CliRunner()
    content_file = tmp_path / "notify.md"
    content_file.write_text("真实测试正文\n\n第二段", encoding="utf-8")
    title = f"[test] ChatTool notify-doc {int(time.time())}"

    result = runner.invoke(
        lark_cli.cli,
        ["notify-doc", title, "--append-file", str(content_file)],
    )

    assert result.exit_code == 0
    assert "文档通知发送成功" in result.output
    assert "document_id:" in result.output
