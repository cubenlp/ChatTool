from types import SimpleNamespace

import pytest

from chattool.client.main import cli


pytestmark = pytest.mark.mock_cli


def test_chattool_zulip_topics_prompts_for_stream(runner, monkeypatch):
    monkeypatch.setattr(
        "chattool.interaction.policy.is_interactive_available", lambda: True
    )
    monkeypatch.setattr(
        "chattool.interaction.command_schema.ask_text",
        lambda message, default="", password=False, style=None: "general",
    )

    client = SimpleNamespace(
        list_subscriptions=lambda: [{"name": "general", "stream_id": 1}],
        list_streams=lambda include_public=True: [{"name": "general", "stream_id": 1}],
        list_topics=lambda stream_id: [{"name": "release", "max_id": 42}],
    )
    monkeypatch.setattr("chattool.tools.zulip.cli._get_client", lambda: client)

    result = runner.invoke(cli, ["zulip", "topics"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "release (max_id=42)" in result.output


def test_chattool_zulip_topic_prompts_for_stream_and_topic(runner, monkeypatch):
    answers = {"stream": "general", "topic": "release"}
    monkeypatch.setattr(
        "chattool.interaction.policy.is_interactive_available", lambda: True
    )
    monkeypatch.setattr(
        "chattool.interaction.command_schema.ask_text",
        lambda message, default="", password=False, style=None: answers[message],
    )

    client = SimpleNamespace(
        get_topic_messages=lambda stream, topic: [
            {
                "timestamp": 1710000000,
                "sender_full_name": "rex",
                "content": "ship it",
            }
        ]
    )
    monkeypatch.setattr("chattool.tools.zulip.cli._get_client", lambda: client)

    result = runner.invoke(cli, ["zulip", "topic"], catch_exceptions=False)

    assert result.exit_code == 0
    assert "# general / release" in result.output
    assert "ship it" in result.output


def test_chattool_zulip_topics_errors_with_no_interaction(runner):
    result = runner.invoke(cli, ["zulip", "topics", "-I"])

    assert result.exit_code != 0
    assert "Missing required value: stream" in result.output
