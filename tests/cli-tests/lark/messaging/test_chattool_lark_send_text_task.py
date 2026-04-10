import json

import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def test_chattool_lark_send_text_task(lark_testkit):
    if not lark_testkit.default_receiver_id:
        pytest.skip("FEISHU_DEFAULT_RECEIVER_ID is required for default send coverage")

    default_text = lark_testkit.unique_name("send-default")
    default_result = lark_testkit.invoke("lark", "send", default_text)
    default_message_id = lark_testkit.message_id_from_output(default_result.output)
    assert default_message_id

    get_default = lark_testkit.bot.get_message(default_message_id)
    assert get_default.success(), f"get_message failed: {get_default.code} {get_default.msg}"
    default_body = json.loads(get_default.data.items[0].body.content)
    assert default_body["text"] == default_text

    explicit_receiver = lark_testkit.message_receiver_id
    explicit_text = lark_testkit.unique_name("send-explicit")
    explicit_result = lark_testkit.invoke("lark", "send", explicit_receiver, explicit_text)
    explicit_message_id = lark_testkit.message_id_from_output(explicit_result.output)
    assert explicit_message_id

    get_explicit = lark_testkit.bot.get_message(explicit_message_id)
    assert get_explicit.success(), f"get_message failed: {get_explicit.code} {get_explicit.msg}"
    explicit_body = json.loads(get_explicit.data.items[0].body.content)
    assert explicit_body["text"] == explicit_text

