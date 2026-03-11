import time
from types import SimpleNamespace

import pytest
from click.testing import CliRunner

from chattool.cli.main import cli


class FakeZulipClient:
    def list_subscriptions(self):
        return [{"name": "general"}]

    def list_streams(self, include_public=False):
        return [{"name": "general"}]

    def get_messages(self, anchor="newest", num_before=20, num_after=0, narrow=None):
        now = int(time.time())
        return [
            {
                "timestamp": now,
                "display_recipient": "general",
                "subject": "announcements",
                "sender_full_name": "alice",
                "content": "Hello community",
            }
        ]

    def get_profile(self):
        return {"email": "bot@example.com"}


class FakeChat:
    def __init__(self, messages=None):
        self.messages = messages or []

    def get_response(self, **kwargs):
        return SimpleNamespace(content="- Summary item 1\n- Summary item 2")


@pytest.fixture()
def runner():
    return CliRunner()


def test_zulip_help_has_no_send(runner):
    result = runner.invoke(cli, ["zulip", "--help"])
    assert result.exit_code == 0
    assert "send" not in result.output


def test_zulip_news_writes_markdown(monkeypatch, runner, tmp_path):
    from chattool.cli.client import zulip as zulip_cli

    monkeypatch.setattr(zulip_cli, "ZulipClient", FakeZulipClient)
    monkeypatch.setattr(zulip_cli, "Chat", FakeChat)

    out_path = tmp_path / "zulip-news.md"
    result = runner.invoke(
        cli,
        ["zulip", "news", "--since-hours", "1", "--stream", "general", "--output", str(out_path)],
    )
    assert result.exit_code == 0
    assert out_path.exists()
    content = out_path.read_text(encoding="utf-8")
    assert "Zulip News" in content
    assert "Summary item" in content


def test_zulip_news_fallback_on_llm_error(monkeypatch, runner, tmp_path):
    from chattool.cli.client import zulip as zulip_cli

    class FailingChat(FakeChat):
        def get_response(self, **kwargs):
            raise RuntimeError("LLM error")

    monkeypatch.setattr(zulip_cli, "ZulipClient", FakeZulipClient)
    monkeypatch.setattr(zulip_cli, "Chat", FailingChat)

    out_path = tmp_path / "zulip-news.md"
    result = runner.invoke(
        cli,
        ["zulip", "news", "--since-hours", "1", "--stream", "general", "--output", str(out_path)],
    )
    assert result.exit_code == 0
    assert "LLM summary failed" in result.output
    content = out_path.read_text(encoding="utf-8")
    assert "Rule-based summary" in content
