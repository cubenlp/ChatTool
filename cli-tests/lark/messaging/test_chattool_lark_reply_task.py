import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def test_chattool_lark_reply_task(lark_testkit):
    if not lark_testkit.message_receiver_id:
        pytest.skip("No Feishu receiver configured for reply coverage")

    seed_text = lark_testkit.unique_name("reply-seed")
    seed_result = lark_testkit.invoke("lark", "send", lark_testkit.message_receiver_id, seed_text)
    seed_message_id = lark_testkit.message_id_from_output(seed_result.output)
    assert seed_message_id

    reply_result = lark_testkit.invoke("lark", "reply", seed_message_id, "收到")
    reply_message_id = lark_testkit.message_id_from_output(reply_result.output)
    assert "回复成功" in reply_result.output
    assert reply_message_id

