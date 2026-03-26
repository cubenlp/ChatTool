from __future__ import annotations


def test_chattool_lark_bitable_field_properties(lark_docaudit):
    text = lark_docaudit.read("skills/feishu/bitable/references/field-properties.md")
    assert "property" in text
    help_output = lark_docaudit.invoke_help("lark", "bitable", "field")
    assert "create" in help_output
    assert "list" in help_output

