import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def test_chattool_lark_doc_fetch_task(lark_testkit):
    created = lark_testkit.create_document(prefix="cli-doc-task-fetch")
    marker = lark_testkit.unique_name("fetch-marker")

    append = lark_testkit.invoke(
        "lark",
        "doc",
        "append-text",
        created.document_id,
        marker,
    )
    assert "追加成功" in append.output

    get_result = lark_testkit.invoke("lark", "doc", "get", created.document_id)
    assert created.document_id in get_result.output
    assert created.title in get_result.output

    raw = lark_testkit.wait_doc_raw_contains(created.document_id, marker)
    assert marker in raw.output

    blocks = lark_testkit.invoke("lark", "doc", "blocks", created.document_id)
    assert "获取成功" in blocks.output
    assert "block_id=" in blocks.output

