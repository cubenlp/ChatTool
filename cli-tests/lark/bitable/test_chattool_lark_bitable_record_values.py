from __future__ import annotations


def test_chattool_lark_bitable_record_values(lark_docaudit):
    text = lark_docaudit.read("skills/feishu/bitable/references/record-values.md")
    for token in ["人员", "日期", "单选", "多选", "附件"]:
        assert token in text
    help_output = lark_docaudit.invoke_help("lark", "bitable", "record")
    for command in ["list", "create", "batch-create"]:
        assert command in help_output

