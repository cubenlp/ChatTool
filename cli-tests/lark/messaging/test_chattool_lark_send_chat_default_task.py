import json

import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def test_chattool_lark_send_chat_default_task(lark_testkit):
    if not lark_testkit.default_chat_id:
        pytest.skip("FEISHU_DEFAULT_CHAT_ID is required for default group send coverage")

    group_text = lark_testkit.unique_name("send-default-chat")
    group_result = lark_testkit.invoke("lark", "send", "-t", "chat_id", group_text)
    group_message_id = lark_testkit.message_id_from_output(group_result.output)
    assert group_message_id

    get_group = lark_testkit.bot.get_message(group_message_id)
    assert get_group.success(), f"get_message failed: {get_group.code} {get_group.msg}"
    group_body = json.loads(get_group.data.items[0].body.content)
    assert group_body["text"] == group_text
