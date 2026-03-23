import re
import time

import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def test_chattool_lark_doc_basic(lark_testkit):
    title = lark_testkit.unique_name("cli-doc")

    document_id = None
    create_output = ""
    for _ in range(3):
        create = lark_testkit.invoke("lark", "doc", "create", title)
        create_output = create.output
        match = re.search(r"document_id[:=]\s*([A-Za-z0-9_]+)", create_output)
        if match:
            document_id = match.group(1)
        if document_id:
            break
        time.sleep(1)

    assert "文档创建成功" in create_output, create_output
    assert document_id

    get_result = lark_testkit.invoke("lark", "doc", "get", document_id)
    assert document_id in get_result.output
    assert title in get_result.output

    append_text = lark_testkit.invoke(
        "lark",
        "doc",
        "append-text",
        document_id,
        "hello from cli doc basic",
    )
    assert "追加成功" in append_text.output

    raw = lark_testkit.invoke("lark", "doc", "raw", document_id)
    assert "hello from cli doc basic" in raw.output

    blocks = lark_testkit.invoke("lark", "doc", "blocks", document_id)
    assert "获取成功" in blocks.output
    assert "block_id=" in blocks.output
