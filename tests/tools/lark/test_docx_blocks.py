import pytest

from chattool.tools.lark.docx_blocks import (
    DocxBlockType,
    make_bullet_block,
    make_callout_block,
    make_code_block,
    make_divider_block,
    make_heading_block,
    make_ordered_block,
    make_quote_block,
    make_text_block,
)


@pytest.mark.lark
class TestDocxBlocks:
    def test_make_text_block(self):
        block = make_text_block("hello")
        assert block == {
            "block_type": DocxBlockType.TEXT,
            "text": {"elements": [{"text_run": {"content": "hello"}}]},
        }

    def test_make_heading_block_clamps_level(self):
        block = make_heading_block("标题", level=20)
        assert block["block_type"] == DocxBlockType.HEADING9
        assert block["heading9"]["elements"][0]["text_run"]["content"] == "标题"

    def test_make_list_blocks(self):
        bullet = make_bullet_block("条目一")
        ordered = make_ordered_block("步骤一")
        assert bullet["block_type"] == DocxBlockType.BULLET
        assert ordered["block_type"] == DocxBlockType.ORDERED

    def test_make_code_block_with_language(self):
        block = make_code_block("print('hi')", language="Python")
        assert block["block_type"] == DocxBlockType.CODE
        assert block["code"]["style"]["language"] == "Python"

    def test_make_quote_block(self):
        block = make_quote_block("引用内容")
        assert block["block_type"] == DocxBlockType.QUOTE
        assert block["quote"]["elements"][0]["text_run"]["content"] == "引用内容"

    def test_make_callout_block(self):
        block = make_callout_block("注意事项", emoji="smile", background_color=5)
        assert block["block_type"] == DocxBlockType.CALLOUT
        assert block["callout"]["callout"]["emoji_id"] == "smile"
        assert block["callout"]["callout"]["background_color"] == 5

    def test_make_divider_block(self):
        block = make_divider_block()
        assert block == {
            "block_type": DocxBlockType.DIVIDER,
            "divider": {},
        }
