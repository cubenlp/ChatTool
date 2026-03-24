from __future__ import annotations


def test_chattool_lark_docx_adoption(lark_docaudit):
    text = lark_docaudit.read("skills/feishu/documents/feishu-docx-adoption-notes.md")
    assert "cli-tests/lark/documents/*.md" in text
    assert "高频、稳定、可复用" in text
    assert "block API" in text

