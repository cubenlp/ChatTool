from __future__ import annotations


def test_chattool_lark_bitable_examples(lark_docaudit):
    text = lark_docaudit.read("skills/feishu/bitable/references/examples.md")
    help_output = lark_docaudit.invoke_help("lark", "bitable")
    for command in ["app", "table", "field", "record"]:
        assert command in help_output
    assert "场景" in text or "示例" in text

