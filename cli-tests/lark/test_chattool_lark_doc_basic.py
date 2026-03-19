from types import SimpleNamespace

import pytest
from click.testing import CliRunner

import chattool.tools.lark.cli as lark_cli


pytestmark = [pytest.mark.e2e, pytest.mark.lark]


class _FakeDocBot:
    appended_texts = None

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
        self.appended_texts = texts
        return SimpleNamespace(
            code=0,
            data=SimpleNamespace(
                document_revision_id=3,
                children=[SimpleNamespace(block_id="blk_new") for _ in texts],
            ),
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
