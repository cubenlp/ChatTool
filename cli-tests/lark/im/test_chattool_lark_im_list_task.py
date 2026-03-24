import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def test_chattool_lark_im_list_task(lark_testkit):
    if not lark_testkit.message_receiver_id:
        pytest.skip("No Feishu receiver configured for IM list task coverage")

    text = lark_testkit.unique_name("im-list-task")
    send_resp = lark_testkit.bot.send_text(
        lark_testkit.message_receiver_id,
        lark_testkit.message_receiver_type,
        text,
    )
    assert send_resp.success(), f"send_text failed: {send_resp.code} {send_resp.msg}"

    get_resp = lark_testkit.bot.get_message(send_resp.data.message_id)
    assert get_resp.success(), f"get_message failed: {get_resp.code} {get_resp.msg}"
    chat_id = get_resp.data.items[0].chat_id

    list_result = lark_testkit.invoke(
        "lark",
        "im",
        "list",
        "--chat-id",
        chat_id,
        "--relative-hours",
        "24",
        "--page-size",
        "50",
    )
    assert "消息列表获取成功" in list_result.output
    payload = lark_testkit.parse_json(list_result.output)
    items = payload.get("data", {}).get("items", [])
    assert items
    assert isinstance(items, list)
