from __future__ import annotations


def test_chattool_lark_api_reference(lark_docaudit):
    text = lark_docaudit.read("skills/feishu/guide/api-reference.md")
    assert "Bot info" in text
    assert "Send message" in text
    assert "Reply message" in text
    assert "Docx document" in text

