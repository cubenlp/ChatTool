import json

import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def test_chattool_lark_send_card_task(lark_testkit):
    if not lark_testkit.default_receiver_id:
        pytest.skip("FEISHU_DEFAULT_RECEIVER_ID is required for card send coverage")

    static_card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "Pytest Card"},
            "template": "blue",
        },
        "elements": [{"tag": "markdown", "content": "static card"}],
    }
    static_path = lark_testkit.tmp_path / "card.json"
    static_path.write_text(json.dumps(static_card, ensure_ascii=False), encoding="utf-8")

    static_result = lark_testkit.invoke("lark", "send", "--card", str(static_path))
    static_message_id = lark_testkit.message_id_from_output(static_result.output)
    assert static_message_id
    static_message = lark_testkit.bot.get_message(static_message_id)
    assert static_message.success(), f"get_message failed: {static_message.code} {static_message.msg}"

    action_card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "Pytest Action Card"},
            "template": "green",
        },
        "elements": [
            {"tag": "markdown", "content": "button card"},
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "Open"},
                        "type": "default",
                        "url": "https://open.feishu.cn",
                    }
                ],
            },
        ],
    }
    action_path = lark_testkit.tmp_path / "card-with-url.json"
    action_path.write_text(json.dumps(action_card, ensure_ascii=False), encoding="utf-8")

    action_result = lark_testkit.invoke("lark", "send", "--card", str(action_path))
    action_message_id = lark_testkit.message_id_from_output(action_result.output)
    assert action_message_id
    action_message = lark_testkit.bot.get_message(action_message_id)
    assert action_message.success(), f"get_message failed: {action_message.code} {action_message.msg}"

