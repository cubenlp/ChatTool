import json
import re
import time

import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def test_chattool_lark_doc_markdown(lark_testkit):
    markdown_path = lark_testkit.tmp_path / "doc.md"
    markdown_path.write_text(
        "# Weekly Report\n\n"
        "- item one\n"
        "- item two\n\n"
        "> quoted note\n\n"
        "```python\nprint('hello')\n```\n",
        encoding="utf-8",
    )

    parse_result = lark_testkit.invoke("lark", "doc", "parse-md", str(markdown_path))
    blocks = json.loads(parse_result.output)
    assert isinstance(blocks, list)
    assert blocks

    document_id = None
    create_output = ""
    for _ in range(3):
        create = lark_testkit.invoke("lark", "doc", "create", lark_testkit.unique_name("cli-doc-md"))
        create_output = create.output
        match = re.search(r"document_id[:=]\s*([A-Za-z0-9_]+)", create_output)
        if match:
            document_id = match.group(1)
        if document_id:
            break
        time.sleep(1)

    assert "文档创建成功" in create_output, create_output
    assert document_id

    blocks_path = lark_testkit.tmp_path / "blocks.json"
    blocks_path.write_text(json.dumps(blocks, ensure_ascii=False, indent=2), encoding="utf-8")

    append_json = lark_testkit.invoke(
        "lark",
        "doc",
        "append-json",
        document_id,
        str(blocks_path),
    )
    assert "JSON 追加成功" in append_json.output

    append_file = lark_testkit.invoke(
        "lark",
        "doc",
        "append-file",
        document_id,
        str(markdown_path),
    )
    assert "文件追加成功" in append_file.output

    if lark_testkit.message_receiver_id:
        notify = lark_testkit.invoke(
            "lark",
            "notify-doc",
            lark_testkit.unique_name("cli-notify-doc"),
            "--append-file",
            str(markdown_path),
        )
        assert "文档通知发送成功" in notify.output
        assert "document_id:" in notify.output
