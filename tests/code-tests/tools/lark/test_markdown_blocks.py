import pytest

from chattool.tools.lark.docx_blocks import DocxBlockType
from chattool.tools.lark.markdown_blocks import parse_markdown_blocks


@pytest.mark.lark
class TestMarkdownBlocks:
    def test_parse_headings_and_paragraphs(self):
        blocks = parse_markdown_blocks("# 标题\n\n第一段\n第二行\n")
        assert len(blocks) == 2
        assert blocks[0]["block_type"] == DocxBlockType.HEADING1
        assert blocks[1]["block_type"] == DocxBlockType.TEXT
        assert blocks[1]["text"]["elements"][0]["text_run"]["content"] == "第一段 第二行"

    def test_parse_lists(self):
        blocks = parse_markdown_blocks("- 条目一\n- 条目二\n1. 步骤一\n2. 步骤二\n")
        assert [block["block_type"] for block in blocks] == [
            DocxBlockType.BULLET,
            DocxBlockType.BULLET,
            DocxBlockType.ORDERED,
            DocxBlockType.ORDERED,
        ]

    def test_parse_quote_and_divider(self):
        blocks = parse_markdown_blocks("> 第一行\n> 第二行\n\n---\n")
        assert blocks[0]["block_type"] == DocxBlockType.QUOTE
        assert blocks[0]["quote"]["elements"][0]["text_run"]["content"] == "第一行\n第二行"
        assert blocks[1]["block_type"] == DocxBlockType.DIVIDER

    def test_parse_code_fence(self):
        blocks = parse_markdown_blocks("```python\nprint('hi')\nprint('bye')\n```\n")
        assert len(blocks) == 1
        assert blocks[0]["block_type"] == DocxBlockType.CODE
        assert blocks[0]["code"]["style"]["language"] == "python"
        assert blocks[0]["code"]["elements"][0]["text_run"]["content"] == "print('hi')\nprint('bye')"

    def test_parse_mixed_blocks(self):
        blocks = parse_markdown_blocks("## 小节\n\n正文\n\n> 引用\n\n- 条目\n")
        assert [block["block_type"] for block in blocks] == [
            DocxBlockType.HEADING2,
            DocxBlockType.TEXT,
            DocxBlockType.QUOTE,
            DocxBlockType.BULLET,
        ]
