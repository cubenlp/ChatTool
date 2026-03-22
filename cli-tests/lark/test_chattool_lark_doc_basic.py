from types import SimpleNamespace

import pytest
from click.testing import CliRunner

import chattool.tools.lark.cli as lark_cli


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


class _FakeDocBot:
    appended_texts = None
    appended_blocks = None
    fail_multi_append = False

    def create_doc_document(self, title, folder_token=None):
        return SimpleNamespace(
            code=0,
            data=SimpleNamespace(
                document=SimpleNamespace(
                    document_id="doc_test_123",
                    title=title,
                    revision_id=1,
                )
            ),
        )

    def get_doc_document(self, document_id):
        return SimpleNamespace(
            code=0,
            data=SimpleNamespace(
                document=SimpleNamespace(
                    document_id=document_id,
                    title="测试文档",
                    revision_id=2,
                )
            ),
        )

    def get_doc_raw_content(self, document_id, lang=None):
        return SimpleNamespace(
            code=0,
            data=SimpleNamespace(content="第一行\n第二行"),
        )

    def get_doc_block_children(self, document_id, block_id, page_size=None, page_token=None, with_descendants=False):
        return SimpleNamespace(
            code=0,
            data=SimpleNamespace(
                items=[
                    SimpleNamespace(block_id="blk_1", block_type=1, children=["blk_2"]),
                    SimpleNamespace(block_id="blk_2", block_type=2, children=[]),
                ],
                has_more=False,
                page_token="",
            ),
        )

    def append_doc_text(self, document_id, text, block_id=None, index=None):
        return SimpleNamespace(
            code=0,
            data=SimpleNamespace(
                document_revision_id=3,
                children=[SimpleNamespace(block_id="blk_new")],
            ),
        )

    def append_doc_texts(self, document_id, texts, block_id=None, index=None):
        if self.fail_multi_append and len(texts) > 1:
            return SimpleNamespace(code=99992402, msg="field validation failed")
        self.appended_texts = texts
        return SimpleNamespace(
            code=0,
            data=SimpleNamespace(
                document_revision_id=3,
                children=[SimpleNamespace(block_id="blk_new") for _ in texts],
            ),
        )

    def append_doc_texts_safe(self, document_id, texts, block_id=None, index=None, batch_size=20):
        children = []
        revision_id = None
        for offset in range(0, len(texts), batch_size):
            chunk = texts[offset: offset + batch_size]
            resp = self.append_doc_texts(document_id, chunk, block_id=block_id, index=index)
            if getattr(resp, "code", 0) == 0:
                revision_id = getattr(resp.data, "document_revision_id", revision_id)
                children.extend(getattr(resp.data, "children", []) or [])
                continue
            for text in chunk:
                single_resp = self.append_doc_text(document_id, text, block_id=block_id, index=index)
                if getattr(single_resp, "code", 0) != 0:
                    return single_resp
                self.appended_texts = (self.appended_texts or []) + [text]
                revision_id = getattr(single_resp.data, "document_revision_id", revision_id)
                children.extend(getattr(single_resp.data, "children", []) or [])
        return SimpleNamespace(
            code=0,
            data=SimpleNamespace(document_revision_id=revision_id, children=children),
            success=lambda: True,
        )

    def append_doc_blocks(self, document_id, blocks, block_id=None, index=None):
        self.appended_blocks = blocks
        return SimpleNamespace(
            code=0,
            data=SimpleNamespace(
                document_revision_id=4,
                children=[SimpleNamespace(block_id=f"blk_{i}") for i, _ in enumerate(blocks, start=1)],
            ),
        )

    def append_doc_blocks_safe(self, document_id, blocks, block_id=None, index=None, batch_size=20):
        children = []
        revision_id = None
        for offset in range(0, len(blocks), batch_size):
            chunk = blocks[offset: offset + batch_size]
            resp = self.append_doc_blocks(document_id, chunk, block_id=block_id, index=index)
            revision_id = getattr(resp.data, "document_revision_id", revision_id)
            children.extend(getattr(resp.data, "children", []) or [])
        return SimpleNamespace(
            code=0,
            data=SimpleNamespace(document_revision_id=revision_id, children=children),
            success=lambda: True,
        )

    def get_doc_meta(self, document_id, with_url=True):
        return SimpleNamespace(
            code=0,
            data=SimpleNamespace(
                metas=[
                    SimpleNamespace(
                        url=f"https://example.feishu.cn/docx/{document_id}",
                    )
                ]
            ),
        )

    def send_text(self, receiver, id_type, text):
        assert receiver == "f25gc16d"
        assert id_type == "user_id"
        assert "https://example.feishu.cn/docx/doc_test_123" in text
        return SimpleNamespace(
            code=0,
            data=SimpleNamespace(message_id="om_notify_123"),
        )


def test_lark_doc_create(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr(lark_cli, "_load_runtime_env", lambda env_ref: None)
    monkeypatch.setattr(lark_cli, "_get_bot", lambda: _FakeDocBot())

    result = runner.invoke(lark_cli.cli, ["doc", "create", "测试文档"])

    assert result.exit_code == 0
    assert "document_id=doc_test_123" in result.output


def test_lark_doc_get_raw_blocks_and_append(monkeypatch):
    runner = CliRunner()
    monkeypatch.setattr(lark_cli, "_load_runtime_env", lambda env_ref: None)
    monkeypatch.setattr(lark_cli, "_get_bot", lambda: _FakeDocBot())

    result = runner.invoke(lark_cli.cli, ["doc", "get", "doc_test_123"])
    assert result.exit_code == 0
    assert "测试文档" in result.output

    result = runner.invoke(lark_cli.cli, ["doc", "raw", "doc_test_123"])
    assert result.exit_code == 0
    assert "第一行" in result.output

    result = runner.invoke(lark_cli.cli, ["doc", "blocks", "doc_test_123"])
    assert result.exit_code == 0
    assert "blk_1" in result.output

    result = runner.invoke(
        lark_cli.cli,
        ["doc", "append-text", "doc_test_123", "hello"],
    )
    assert result.exit_code == 0
    assert "追加成功" in result.output


def test_lark_notify_doc_uses_default_receiver(monkeypatch):
    runner = CliRunner()
    fake_bot = _FakeDocBot()
    monkeypatch.setattr(lark_cli, "_load_runtime_env", lambda env_ref: None)
    monkeypatch.setattr(lark_cli, "_get_bot", lambda: fake_bot)
    monkeypatch.setattr(
        lark_cli.FeishuConfig,
        "FEISHU_DEFAULT_RECEIVER_ID",
        type("Field", (), {"value": "f25gc16d"})(),
    )

    result = runner.invoke(
        lark_cli.cli,
        ["notify-doc", "测试通知文档", "这里是正文"],
    )

    assert result.exit_code == 0
    assert "文档通知发送成功" in result.output
    assert "doc_test_123" in result.output
    assert fake_bot.appended_texts == ["这里是正文"]


def test_lark_notify_doc_supports_append_file_and_open(tmp_path, monkeypatch):
    runner = CliRunner()
    fake_bot = _FakeDocBot()
    content_file = tmp_path / "notify.md"
    content_file.write_text("第一行\n\n第二行\n", encoding="utf-8")
    opened = []

    monkeypatch.setattr(lark_cli, "_load_runtime_env", lambda env_ref: None)
    monkeypatch.setattr(lark_cli, "_get_bot", lambda: fake_bot)
    monkeypatch.setattr(
        lark_cli.FeishuConfig,
        "FEISHU_DEFAULT_RECEIVER_ID",
        type("Field", (), {"value": "f25gc16d"})(),
    )
    monkeypatch.setattr(lark_cli.click, "launch", lambda url: opened.append(url))

    result = runner.invoke(
        lark_cli.cli,
        ["notify-doc", "文件通知文档", "--append-file", str(content_file), "--open"],
    )

    assert result.exit_code == 0
    assert fake_bot.appended_texts == ["第一行", "第二行"]
    assert opened == ["https://example.feishu.cn/docx/doc_test_123"]


def test_lark_doc_append_file_parses_markdown(tmp_path, monkeypatch):
    runner = CliRunner()
    fake_bot = _FakeDocBot()
    content_file = tmp_path / "doc.md"
    content_file.write_text(
        "# 标题\n\n第一段带有 **强调** 和 [链接](https://example.com)。\n\n- 条目一\n- 条目二\n\n```python\nprint('hi')\n```\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(lark_cli, "_load_runtime_env", lambda env_ref: None)
    monkeypatch.setattr(lark_cli, "_get_bot", lambda: fake_bot)

    result = runner.invoke(
        lark_cli.cli,
        ["doc", "append-file", "doc_test_123", str(content_file)],
    )

    assert result.exit_code == 0
    assert "文件追加成功" in result.output
    assert fake_bot.appended_texts == [
        "标题",
        "第一段带有 强调 和 链接 (https://example.com)。",
        "• 条目一",
        "• 条目二",
        "print('hi')",
    ]


def test_lark_doc_parse_md_outputs_blocks(tmp_path):
    runner = CliRunner()
    content_file = tmp_path / "doc.md"
    content_file.write_text(
        "# 标题\n\n正文\n\n- 条目一\n\n> 引用\n\n```python\nprint('hi')\n```\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        lark_cli.cli,
        ["doc", "parse-md", str(content_file)],
    )

    assert result.exit_code == 0
    assert '"block_type": 3' in result.output
    assert '"block_type": 12' in result.output
    assert '"block_type": 15' in result.output
    assert '"block_type": 14' in result.output


def test_lark_doc_parse_md_supports_output_file(tmp_path):
    runner = CliRunner()
    content_file = tmp_path / "doc.md"
    out_file = tmp_path / "blocks.json"
    content_file.write_text("## 小节\n\n正文\n", encoding="utf-8")

    result = runner.invoke(
        lark_cli.cli,
        ["doc", "parse-md", str(content_file), "--output", str(out_file)],
    )

    assert result.exit_code == 0
    assert "已写入" in result.output
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert '"block_type": 4' in content


def test_lark_doc_append_json(tmp_path, monkeypatch):
    runner = CliRunner()
    fake_bot = _FakeDocBot()
    payload_file = tmp_path / "blocks.json"
    payload_file.write_text(
        '[{"block_type": 3, "heading1": {"elements": [{"text_run": {"content": "标题"}}]}}]',
        encoding="utf-8",
    )

    monkeypatch.setattr(lark_cli, "_load_runtime_env", lambda env_ref: None)
    monkeypatch.setattr(lark_cli, "_get_bot", lambda: fake_bot)

    result = runner.invoke(
        lark_cli.cli,
        ["doc", "append-json", "doc_test_123", str(payload_file)],
    )

    assert result.exit_code == 0
    assert "JSON 追加成功" in result.output
    assert fake_bot.appended_blocks[0]["block_type"] == 3


def test_lark_notify_doc_append_file_falls_back_to_single_append(tmp_path, monkeypatch):
    runner = CliRunner()
    fake_bot = _FakeDocBot()
    fake_bot.fail_multi_append = True
    content_file = tmp_path / "notify.md"
    content_file.write_text("第一行\n\n第二行\n", encoding="utf-8")

    monkeypatch.setattr(lark_cli, "_load_runtime_env", lambda env_ref: None)
    monkeypatch.setattr(lark_cli, "_get_bot", lambda: fake_bot)
    monkeypatch.setattr(
        lark_cli.FeishuConfig,
        "FEISHU_DEFAULT_RECEIVER_ID",
        type("Field", (), {"value": "f25gc16d"})(),
    )

    result = runner.invoke(
        lark_cli.cli,
        ["notify-doc", "文件通知文档", "--append-file", str(content_file), "--batch-size", "5"],
    )

    assert result.exit_code == 0
    assert "文档通知发送成功" in result.output
    assert fake_bot.appended_texts == ["第一行", "第二行"]
