import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def test_chattool_lark_doc_create_notify_task(lark_testkit):
    created = lark_testkit.create_document(prefix="cli-doc-task-create")

    get_result = lark_testkit.invoke("lark", "doc", "get", created.document_id)
    assert created.document_id in get_result.output
    assert created.title in get_result.output

    if not lark_testkit.message_receiver_id:
        pytest.skip("No Feishu receiver configured for notify-doc coverage")

    notify_title = lark_testkit.unique_name("cli-doc-task-notify")
    body_text = lark_testkit.unique_name("notify-body")
    notify = lark_testkit.invoke("lark", "notify-doc", notify_title, body_text)
    document_id = lark_testkit.document_id_from_output(notify.output)

    assert "文档通知发送成功" in notify.output
    assert "url        :" in notify.output

    raw = lark_testkit.wait_doc_raw_contains(document_id, body_text)
    assert body_text in raw.output

