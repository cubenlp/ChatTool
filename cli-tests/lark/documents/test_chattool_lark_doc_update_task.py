def test_chattool_lark_doc_update_task(lark_testkit):
    help_result = lark_testkit.invoke("lark", "doc", "--help")
    assert "update" not in help_result.output

    raw_result = lark_testkit.invoke_raw("lark", "doc", "update")
    assert raw_result.exit_code != 0
    assert "No such command 'update'" in raw_result.output

