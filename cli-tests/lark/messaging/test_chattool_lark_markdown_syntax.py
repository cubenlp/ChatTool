from __future__ import annotations


def test_chattool_lark_markdown_syntax(lark_docaudit):
    text = lark_docaudit.read("skills/feishu/messaging/lark-markdown-syntax.md")
    for snippet in ["chattool lark send --card", "chattool lark send --post", "chattool lark reply", "代码块", "图片"]:
        assert snippet in text

