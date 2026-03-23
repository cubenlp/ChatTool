import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def test_chattool_lark_troubleshoot_basic(lark_testkit):
    info = lark_testkit.invoke("lark", "info")
    assert "名称" in info.output
    assert "激活状态" in info.output

    scopes = lark_testkit.invoke("lark", "scopes", "-f", "im")
    assert "im" in scopes.output.lower()

    doctor = lark_testkit.invoke("lark", "troubleshoot", "doctor")
    assert "Feishu doctor" in doctor.output
    assert "bot_name" in doctor.output

    check_scopes = lark_testkit.invoke("lark", "troubleshoot", "check-scopes")
    assert "scopes 检查完成" in check_scopes.output

    check_events = lark_testkit.invoke("lark", "troubleshoot", "check-events")
    assert "事件订阅检查" in check_events.output

    check_card = lark_testkit.invoke("lark", "troubleshoot", "check-card-action")
    assert "卡片交互检查" in check_card.output
