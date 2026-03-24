import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def test_chattool_lark_troubleshoot_message_task(lark_testkit):
    doctor = lark_testkit.invoke("lark", "troubleshoot", "doctor")
    assert "Feishu doctor" in doctor.output

    check_scopes = lark_testkit.invoke("lark", "troubleshoot", "check-scopes")
    assert "scopes 检查完成" in check_scopes.output

    check_events = lark_testkit.invoke("lark", "troubleshoot", "check-events")
    assert "事件订阅检查" in check_events.output

    check_card = lark_testkit.invoke("lark", "troubleshoot", "check-card-action")
    assert "卡片交互检查" in check_card.output

    if lark_testkit.message_receiver_id:
        send_card = lark_testkit.invoke(
            "lark",
            "troubleshoot",
            "check-scopes",
            "--send-card",
            "--receiver",
            lark_testkit.message_receiver_id,
            "--type",
            lark_testkit.message_receiver_type,
        )
        assert "card_message_id:" in send_card.output

