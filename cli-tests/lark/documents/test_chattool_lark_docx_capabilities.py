from __future__ import annotations


def test_chattool_lark_docx_capabilities(lark_docaudit):
    text = lark_docaudit.read("skills/feishu/documents/official-docx-capabilities.md")
    for command in [
        "notify-doc",
        "doc append-text",
        "doc append-file",
        "doc parse-md",
        "doc append-json",
    ]:
        assert command in text

    help_output = lark_docaudit.invoke_help("lark", "doc")
    for command in ["create", "get", "raw", "blocks", "append-text", "append-file", "parse-md", "append-json"]:
        assert command in help_output

