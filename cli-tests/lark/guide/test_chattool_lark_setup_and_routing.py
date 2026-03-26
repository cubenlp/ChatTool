from __future__ import annotations


def test_chattool_lark_setup_and_routing(lark_docaudit):
    text = lark_docaudit.read("skills/feishu/guide/setup-and-routing.md")
    assert "FEISHU_DEFAULT_RECEIVER_ID" in text
    assert "FEISHU_TEST_USER_ID" in text
    assert "chattool lark bitable" in text
    assert "chattool lark calendar" in text
    assert "chattool lark im" in text
    assert "chattool lark task" in text
    assert "chattool lark troubleshoot" in text

    help_output = lark_docaudit.invoke_help("lark", "info")
    assert "-e" in help_output or "--env" in help_output

