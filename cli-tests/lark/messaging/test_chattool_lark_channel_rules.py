from __future__ import annotations


def test_chattool_lark_channel_rules(lark_docaudit):
    text = lark_docaudit.read("skills/feishu/messaging/channel-rules.md")
    for command in ["chattool lark send", "chattool lark reply", "chattool lark notify-doc", "chattool lark doc"]:
        assert command in text
    assert "Short, conversational" in text

