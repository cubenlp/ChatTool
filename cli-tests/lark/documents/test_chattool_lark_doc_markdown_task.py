import json

import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def test_chattool_lark_doc_markdown_task(lark_testkit):
    markdown_path = lark_testkit.tmp_path / "doc-task.md"
    marker = lark_testkit.unique_name("markdown-task")
    markdown_path.write_text(
        "# Markdown Task\n\n"
        f"{marker}\n\n"
        "- item one\n"
        "> quoted note\n\n"
        "```python\n"
        "print('hello from markdown task')\n"
        "```\n",
        encoding="utf-8",
    )

    parse_result = lark_testkit.invoke("lark", "doc", "parse-md", str(markdown_path))
    blocks = json.loads(parse_result.output)
    assert isinstance(blocks, list)
    assert blocks

    blocks_path = lark_testkit.tmp_path / "doc-task.blocks.json"
    blocks_path.write_text(json.dumps(blocks, ensure_ascii=False, indent=2), encoding="utf-8")

    created = lark_testkit.create_document(prefix="cli-doc-task-markdown")

    append_json = lark_testkit.invoke(
        "lark",
        "doc",
        "append-json",
        created.document_id,
        str(blocks_path),
    )
    assert "JSON 追加成功" in append_json.output

    raw = lark_testkit.wait_doc_raw_contains(created.document_id, marker)
    assert marker in raw.output
