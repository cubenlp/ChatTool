from __future__ import annotations


def test_chattool_lark_overview_zh(lark_docaudit):
    assert lark_docaudit.exists("skills/feishu/guide/overview.zh.md")
    zh_text = lark_docaudit.read("skills/feishu/guide/overview.zh.md")
    en_text = lark_docaudit.read("skills/feishu/guide/overview.md")

    assert "chattool lark" in zh_text
    for phrase in ["info", "scopes", "send", "upload", "reply", "listen", "chat", "doc"]:
        assert phrase in zh_text
        assert phrase in en_text

