import json

import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def test_chattool_lark_send_permission_recovery_task(lark_testkit):
    card_path = lark_testkit.tmp_path / "permission-card.json"
    export_result = lark_testkit.invoke(
        "lark",
        "troubleshoot",
        "check-scopes",
        "--card-file",
        str(card_path),
    )
    assert "scopes 检查完成" in export_result.output
    assert card_path.exists()

    payload = json.loads(card_path.read_text(encoding="utf-8"))
    assert payload["header"]["title"]["content"] == "ChatTool Feishu Scope Check"
    assert payload["elements"][-1]["tag"] == "action"

    if not lark_testkit.message_receiver_id:
        pytest.skip("No Feishu receiver configured for permission card delivery")

    send_result = lark_testkit.invoke(
        "lark",
        "troubleshoot",
        "check-scopes",
        "--send-card",
        "--receiver",
        lark_testkit.message_receiver_id,
        "--type",
        lark_testkit.message_receiver_type,
    )
    assert "card_message_id:" in send_result.output

