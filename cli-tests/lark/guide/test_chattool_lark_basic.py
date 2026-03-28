import json

import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def test_chattool_lark_basic(lark_testkit):
    info = lark_testkit.invoke("lark", "info")
    assert "名称" in info.output
    assert "激活状态" in info.output

    if not lark_testkit.message_receiver_id:
        pytest.skip("No Feishu receiver configured for send coverage")

    text = lark_testkit.unique_name("cli-basic")
    send = lark_testkit.invoke("lark", "send", lark_testkit.message_receiver_id, text)
    message_id = lark_testkit.message_id_from_output(send.output)
    assert message_id

    get_resp = lark_testkit.bot.get_message(message_id)
    assert get_resp.success(), f"get_message failed: {get_resp.code} {get_resp.msg}"
    body = json.loads(get_resp.data.items[0].body.content)
    assert body["text"] == text
