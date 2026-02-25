"""
Unit tests for MessageContext.
All tests run without network access (real bot is mocked).
"""
import json
import pytest
from unittest.mock import MagicMock

from chattool.tools.lark.context import MessageContext


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def make_event(
    msg_type="text",
    content=None,
    message_id="om_abc123",
    chat_id="oc_group1",
    chat_type="group",
    open_id="ou_user1",
    sender_type="user",
    thread_id=None,
):
    if content is None:
        content = json.dumps({"text": "Hello!"}) if msg_type == "text" else "{}"

    msg = MagicMock()
    msg.message_type = msg_type
    msg.content = content
    msg.message_id = message_id
    msg.chat_id = chat_id
    msg.chat_type = chat_type
    msg.thread_id = thread_id

    sid = MagicMock()
    sid.open_id = open_id
    sender = MagicMock()
    sender.sender_id = sid
    sender.sender_type = sender_type

    event = MagicMock()
    event.message = msg
    event.sender = sender

    data = MagicMock()
    data.event = event
    return data


@pytest.fixture
def mock_bot():
    return MagicMock()


# ---------------------------------------------------------------------------
# Basic properties
# ---------------------------------------------------------------------------

@pytest.mark.lark
class TestMessageContextProperties:
    def test_text_from_text_message(self, mock_bot):
        ctx = MessageContext(mock_bot, make_event(content=json.dumps({"text": "你好"})))
        assert ctx.text == "你好"

    def test_text_empty_for_non_text(self, mock_bot):
        ctx = MessageContext(mock_bot, make_event(msg_type="image", content=json.dumps({"image_key": "img_x"})))
        assert ctx.text == ""

    def test_text_empty_on_invalid_json(self, mock_bot):
        ctx = MessageContext(mock_bot, make_event(msg_type="text", content="not-json"))
        assert ctx.text == ""

    def test_msg_type(self, mock_bot):
        ctx = MessageContext(mock_bot, make_event(msg_type="file"))
        assert ctx.msg_type == "file"

    def test_message_id(self, mock_bot):
        ctx = MessageContext(mock_bot, make_event(message_id="om_xyz"))
        assert ctx.message_id == "om_xyz"

    def test_chat_id(self, mock_bot):
        ctx = MessageContext(mock_bot, make_event(chat_id="oc_chat99"))
        assert ctx.chat_id == "oc_chat99"

    def test_chat_type_group(self, mock_bot):
        ctx = MessageContext(mock_bot, make_event(chat_type="group"))
        assert ctx.chat_type == "group"
        assert ctx.is_group is True

    def test_chat_type_p2p(self, mock_bot):
        ctx = MessageContext(mock_bot, make_event(chat_type="p2p"))
        assert ctx.chat_type == "p2p"
        assert ctx.is_group is False

    def test_sender_id(self, mock_bot):
        ctx = MessageContext(mock_bot, make_event(open_id="ou_sender42"))
        assert ctx.sender_id == "ou_sender42"

    def test_sender_type(self, mock_bot):
        ctx = MessageContext(mock_bot, make_event(sender_type="bot"))
        assert ctx.sender_type == "bot"

    def test_thread_id_present(self, mock_bot):
        ctx = MessageContext(mock_bot, make_event(thread_id="omt_thread1"))
        assert ctx.thread_id == "omt_thread1"

    def test_thread_id_none(self, mock_bot):
        ctx = MessageContext(mock_bot, make_event(thread_id=None))
        assert ctx.thread_id is None

    def test_raw_returns_original_data(self, mock_bot):
        data = make_event()
        ctx = MessageContext(mock_bot, data)
        assert ctx.raw is data


# ---------------------------------------------------------------------------
# Reply / send helpers
# ---------------------------------------------------------------------------

@pytest.mark.lark
class TestMessageContextReply:
    def test_reply_delegates_to_bot_reply(self, mock_bot):
        ctx = MessageContext(mock_bot, make_event(message_id="om_m1"))
        ctx.reply("回复内容")
        mock_bot.reply.assert_called_once_with("om_m1", "回复内容")

    def test_reply_card_delegates_to_bot_reply_card(self, mock_bot):
        card = {"schema": "2.0", "body": {}}
        ctx = MessageContext(mock_bot, make_event(message_id="om_m2"))
        ctx.reply_card(card)
        mock_bot.reply_card.assert_called_once_with("om_m2", card)

    def test_send_uses_chat_id(self, mock_bot):
        ctx = MessageContext(mock_bot, make_event(chat_id="oc_chat5"))
        ctx.send("新消息")
        mock_bot.send_text.assert_called_once_with("oc_chat5", "chat_id", "新消息")

    def test_send_card_uses_chat_id(self, mock_bot):
        card = {"schema": "2.0"}
        ctx = MessageContext(mock_bot, make_event(chat_id="oc_chat6"))
        ctx.send_card(card)
        mock_bot.send_card.assert_called_once_with("oc_chat6", "chat_id", card)


# ---------------------------------------------------------------------------
# get_content
# ---------------------------------------------------------------------------

@pytest.mark.lark
class TestMessageContextContent:
    def test_get_content_text(self, mock_bot):
        ctx = MessageContext(mock_bot, make_event(content=json.dumps({"text": "hi"})))
        assert ctx.get_content() == {"text": "hi"}

    def test_get_content_image(self, mock_bot):
        ctx = MessageContext(
            mock_bot,
            make_event(msg_type="image", content=json.dumps({"image_key": "img_k"})),
        )
        assert ctx.get_content() == {"image_key": "img_k"}

    def test_get_content_returns_none_on_bad_json(self, mock_bot):
        ctx = MessageContext(mock_bot, make_event(msg_type="text", content="bad"))
        # text is empty; get_content should also return None gracefully
        assert ctx.get_content() is None

    def test_repr_contains_key_info(self, mock_bot):
        ctx = MessageContext(mock_bot, make_event(msg_type="text", open_id="ou_repr"))
        r = repr(ctx)
        assert "MessageContext" in r
        assert "text" in r
