import pytest


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


def test_chattool_lark_doc_append_task(lark_testkit):
    created = lark_testkit.create_document(prefix="cli-doc-task-append")
    text_marker = lark_testkit.unique_name("append-text")

    append_text = lark_testkit.invoke(
        "lark",
        "doc",
        "append-text",
        created.document_id,
        text_marker,
    )
    assert "追加成功" in append_text.output
    lark_testkit.wait_doc_raw_contains(created.document_id, text_marker)

    markdown_path = lark_testkit.tmp_path / "append.md"
    file_marker = lark_testkit.unique_name("append-file")
    markdown_path.write_text(
        "# Append Task\n\n"
        f"{file_marker}\n\n"
        "- item one\n"
        "- item two\n",
        encoding="utf-8",
    )

    append_file = lark_testkit.invoke(
        "lark",
        "doc",
        "append-file",
        created.document_id,
        str(markdown_path),
    )
    assert "文件追加成功" in append_file.output

    raw = lark_testkit.wait_doc_raw_contains(created.document_id, file_marker)
    assert file_marker in raw.output

