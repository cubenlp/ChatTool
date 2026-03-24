from __future__ import annotations


def test_chattool_lark_overview(lark_docaudit):
    text = lark_docaudit.read("skills/feishu/guide/overview.md")
    assert "chattool lark" in text
    for command in [
        "chattool lark info",
        "chattool lark scopes",
        "chattool lark send",
        "chattool lark upload",
        "chattool lark reply",
        "chattool lark listen",
        "chattool lark chat",
        "chattool lark doc",
    ]:
        assert command in text

    help_output = lark_docaudit.invoke_help("lark")
    for command in ["info", "scopes", "send", "upload", "reply", "listen", "chat", "doc"]:
        assert command in help_output

