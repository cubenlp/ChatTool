import json
import pytest
from unittest.mock import MagicMock, patch, call

from chattool.tools.lark.bot import LarkBot
from chattool.tools.lark.elements import TextMessage, PostMessage
from chattool.config.main import FeishuConfig


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_config(api_base=""):
    cfg = MagicMock(spec=FeishuConfig)
    cfg.FEISHU_APP_ID.value = "fake_app_id"
    cfg.FEISHU_APP_SECRET.value = "fake_app_secret"
    cfg.FEISHU_API_BASE.value = api_base
    return cfg


def _make_event(
    msg_type="text",
    content=None,
    message_id="om_test",
    chat_id="oc_test",
    chat_type="group",
    open_id="ou_test",
    thread_id=None,
):
    """Build a minimal mock P2ImMessageReceiveV1 event."""
    if content is None:
        content = json.dumps({"text": "hello"}) if msg_type == "text" else "{}"

    msg = MagicMock()
    msg.message_type = msg_type
    msg.content = content
    msg.message_id = message_id
    msg.chat_id = chat_id
    msg.chat_type = chat_type
    msg.thread_id = thread_id

    sender_id = MagicMock()
    sender_id.open_id = open_id
    sender = MagicMock()
    sender.sender_id = sender_id
    sender.sender_type = "user"

    event = MagicMock()
    event.message = msg
    event.sender = sender

    data = MagicMock()
    data.event = event
    return data


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def patched_bot():
    """Return a LarkBot whose lark_oapi client is fully mocked."""
    with (
        patch("chattool.tools.lark.bot.lark_oapi") as mock_lark,
        patch("chattool.tools.lark.bot.CreateMessageRequest") as mock_create_req,
        patch("chattool.tools.lark.bot.CreateMessageRequestBody") as mock_create_body,
        patch("chattool.tools.lark.bot.ReplyMessageRequest") as mock_reply_req,
        patch("chattool.tools.lark.bot.ReplyMessageRequestBody") as mock_reply_body,
        patch("chattool.tools.lark.bot.GetChatRequest") as mock_chat_req,
        patch("chattool.tools.lark.bot.GetChatMembersRequest") as mock_members_req,
    ):
        # Build chain mocks
        mock_builder = MagicMock()
        mock_client = MagicMock()
        mock_lark.Client.builder.return_value = mock_builder
        for attr in ("app_id", "app_secret", "log_level", "domain"):
            getattr(mock_builder, attr).return_value = mock_builder
        mock_builder.build.return_value = mock_client

        # CreateMessage mocks
        body_builder = MagicMock()
        mock_create_body.builder.return_value = body_builder
        for attr in ("receive_id", "msg_type", "content", "build"):
            getattr(body_builder, attr).return_value = body_builder
        body_builder.build.return_value = MagicMock(name="msg_body")

        req_builder = MagicMock()
        mock_create_req.builder.return_value = req_builder
        for attr in ("receive_id_type", "request_body", "build"):
            getattr(req_builder, attr).return_value = req_builder
        req_builder.build.return_value = MagicMock(name="msg_req")

        # ReplyMessage mocks
        rbody_builder = MagicMock()
        mock_reply_body.builder.return_value = rbody_builder
        for attr in ("content", "msg_type", "build"):
            getattr(rbody_builder, attr).return_value = rbody_builder
        rbody_builder.build.return_value = MagicMock(name="reply_body")

        rreq_builder = MagicMock()
        mock_reply_req.builder.return_value = rreq_builder
        for attr in ("message_id", "request_body", "build"):
            getattr(rreq_builder, attr).return_value = rreq_builder
        rreq_builder.build.return_value = MagicMock(name="reply_req")

        # Chat info mocks
        chat_builder = MagicMock()
        mock_chat_req.builder.return_value = chat_builder
        for attr in ("chat_id", "user_id_type", "build"):
            getattr(chat_builder, attr).return_value = chat_builder

        members_builder = MagicMock()
        mock_members_req.builder.return_value = members_builder
        for attr in ("chat_id", "member_id_type", "page_size", "page_token", "build"):
            getattr(members_builder, attr).return_value = members_builder

        cfg = _make_config()
        bot = LarkBot(config=cfg)

        yield bot, mock_client, mock_lark


# ---------------------------------------------------------------------------
# Init tests
# ---------------------------------------------------------------------------

@pytest.mark.lark
class TestLarkBotInit:
    def test_init_builds_client(self, patched_bot):
        bot, mock_client, mock_lark = patched_bot
        assert bot.client is mock_client

    def test_init_with_custom_domain(self):
        with patch("chattool.tools.lark.bot.lark_oapi") as mock_lark:
            builder = MagicMock()
            mock_lark.Client.builder.return_value = builder
            for attr in ("app_id", "app_secret", "log_level", "domain"):
                getattr(builder, attr).return_value = builder
            builder.build.return_value = MagicMock()

            cfg = _make_config(api_base="https://open.larksuite.com")
            LarkBot(config=cfg)
            builder.domain.assert_called_with("https://open.larksuite.com")

    def test_init_without_domain_skips_domain_call(self):
        with patch("chattool.tools.lark.bot.lark_oapi") as mock_lark:
            builder = MagicMock()
            mock_lark.Client.builder.return_value = builder
            for attr in ("app_id", "app_secret", "log_level"):
                getattr(builder, attr).return_value = builder
            builder.build.return_value = MagicMock()

            cfg = _make_config(api_base="")
            LarkBot(config=cfg)
            builder.domain.assert_not_called()


# ---------------------------------------------------------------------------
# Send tests
# ---------------------------------------------------------------------------

@pytest.mark.lark
class TestLarkBotSend:
    def test_send_text(self, patched_bot):
        bot, mock_client, _ = patched_bot
        mock_client.im.v1.message.create.return_value = MagicMock(
            success=MagicMock(return_value=True),
            data=MagicMock(message_id="om_1"),
        )
        bot.send_text("ou_user", "open_id", "Hello")
        mock_client.im.v1.message.create.assert_called_once()

    def test_send_post(self, patched_bot):
        bot, mock_client, _ = patched_bot
        mock_client.im.v1.message.create.return_value = MagicMock(
            success=MagicMock(return_value=True)
        )
        bot.send_post("oc_chat", "chat_id", {"zh_cn": {"title": "T", "content": [[]]}})
        mock_client.im.v1.message.create.assert_called_once()

    def test_send_image(self, patched_bot):
        bot, mock_client, _ = patched_bot
        mock_client.im.v1.message.create.return_value = MagicMock(
            success=MagicMock(return_value=True)
        )
        bot.send_image("oc_chat", "chat_id", "img_key_abc")
        mock_client.im.v1.message.create.assert_called_once()

    def test_send_card(self, patched_bot):
        bot, mock_client, _ = patched_bot
        mock_client.im.v1.message.create.return_value = MagicMock(
            success=MagicMock(return_value=True)
        )
        bot.send_card("ou_user", "open_id", {"schema": "2.0", "body": {}})
        mock_client.im.v1.message.create.assert_called_once()

    def test_send_message_object(self, patched_bot):
        bot, mock_client, _ = patched_bot
        mock_client.im.v1.message.create.return_value = MagicMock(
            success=MagicMock(return_value=True)
        )
        msg = TextMessage("Hello via object")
        bot.send_message("ou_user", "open_id", msg)
        mock_client.im.v1.message.create.assert_called_once()

    def test_send_logs_error_on_failure(self, patched_bot):
        bot, mock_client, mock_lark = patched_bot
        mock_client.im.v1.message.create.return_value = MagicMock(
            success=MagicMock(return_value=False),
            code=99991401,
            msg="Invalid token",
            get_log_id=MagicMock(return_value="log_1"),
        )
        bot.send_text("ou_user", "open_id", "Test")
        mock_lark.logger.error.assert_called()


# ---------------------------------------------------------------------------
# Reply tests
# ---------------------------------------------------------------------------

@pytest.mark.lark
class TestLarkBotReply:
    def test_reply_text(self, patched_bot):
        bot, mock_client, _ = patched_bot
        mock_client.im.v1.message.reply.return_value = MagicMock(
            success=MagicMock(return_value=True)
        )
        bot.reply("om_msg1", "回复内容")
        mock_client.im.v1.message.reply.assert_called_once()

    def test_reply_card(self, patched_bot):
        bot, mock_client, _ = patched_bot
        mock_client.im.v1.message.reply.return_value = MagicMock(
            success=MagicMock(return_value=True)
        )
        bot.reply_card("om_msg1", {"schema": "2.0"})
        mock_client.im.v1.message.reply.assert_called_once()

    def test_reply_logs_error_on_failure(self, patched_bot):
        bot, mock_client, mock_lark = patched_bot
        mock_client.im.v1.message.reply.return_value = MagicMock(
            success=MagicMock(return_value=False),
            code=400,
            msg="Bad request",
            get_log_id=MagicMock(return_value="log_2"),
        )
        bot.reply("om_msg1", "text")
        mock_lark.logger.error.assert_called()


# ---------------------------------------------------------------------------
# Message dispatch tests
# ---------------------------------------------------------------------------

@pytest.mark.lark
class TestLarkBotDispatch:
    def test_on_message_handler_called(self, patched_bot):
        bot, mock_client, _ = patched_bot
        received = []

        @bot.on_message
        def handle(ctx):
            received.append(ctx.text)

        event = _make_event(content=json.dumps({"text": "hi"}))
        bot._dispatch_message(event)
        assert received == ["hi"]

    def test_on_message_with_decorator_args(self, patched_bot):
        bot, _, _ = patched_bot
        received = []

        @bot.on_message(group_only=True)
        def group_handle(ctx):
            received.append("group")

        # Group message → should fire
        bot._dispatch_message(_make_event(chat_type="group"))
        assert received == ["group"]

        # Private message → should NOT fire
        bot._dispatch_message(_make_event(chat_type="p2p"))
        assert received == ["group"]

    def test_command_handler_fires_on_slash(self, patched_bot):
        bot, _, _ = patched_bot
        received = []

        @bot.command("/help")
        def on_help(ctx):
            received.append("help")

        bot._dispatch_message(_make_event(content=json.dumps({"text": "/help"})))
        assert received == ["help"]

    def test_command_takes_priority_over_on_message(self, patched_bot):
        bot, _, _ = patched_bot
        order = []

        @bot.command("/go")
        def cmd(ctx):
            order.append("cmd")

        @bot.on_message
        def fallback(ctx):
            order.append("fallback")

        bot._dispatch_message(_make_event(content=json.dumps({"text": "/go"})))
        assert order == ["cmd"]

    def test_fallback_fires_for_non_command(self, patched_bot):
        bot, _, _ = patched_bot
        order = []

        @bot.command("/go")
        def cmd(ctx):
            order.append("cmd")

        @bot.on_message
        def fallback(ctx):
            order.append("fallback")

        bot._dispatch_message(_make_event(content=json.dumps({"text": "ordinary message"})))
        assert order == ["fallback"]

    def test_regex_handler(self, patched_bot):
        bot, _, _ = patched_bot
        matches = []

        @bot.regex(r"^查询\s+(.+)$")
        def on_query(ctx):
            matches.append(ctx._match.group(1))

        bot._dispatch_message(_make_event(content=json.dumps({"text": "查询 天气"})))
        assert matches == ["天气"]

    def test_regex_no_match_falls_through(self, patched_bot):
        bot, _, _ = patched_bot
        fired = []

        @bot.regex(r"^查询")
        def on_query(ctx):
            fired.append("regex")

        @bot.on_message
        def fallback(ctx):
            fired.append("fallback")

        bot._dispatch_message(_make_event(content=json.dumps({"text": "普通消息"})))
        assert fired == ["fallback"]

    def test_handler_exception_does_not_propagate(self, patched_bot):
        bot, _, mock_lark = patched_bot

        @bot.on_message
        def bad_handler(ctx):
            raise ValueError("intentional error")

        # Should NOT raise
        bot._dispatch_message(_make_event())
        mock_lark.logger.error.assert_called()

    def test_multiple_handlers_first_match_wins(self, patched_bot):
        bot, _, _ = patched_bot
        order = []

        @bot.on_message
        def first(ctx):
            order.append("first")

        @bot.on_message
        def second(ctx):
            order.append("second")

        bot._dispatch_message(_make_event())
        assert order == ["first"]

    def test_on_bot_added_called(self, patched_bot):
        bot, _, _ = patched_bot
        called_with = []

        @bot.on_bot_added
        def welcome(chat_id):
            called_with.append(chat_id)

        mock_data = MagicMock()
        mock_data.event.chat_id = "oc_new_group"
        # Simulate firing the registered handler directly
        for h in bot._bot_added_handlers:
            h("oc_new_group")

        assert called_with == ["oc_new_group"]


# ---------------------------------------------------------------------------
# Chat info tests
# ---------------------------------------------------------------------------

@pytest.mark.lark
class TestLarkBotChatInfo:
    def test_get_chat_info(self, patched_bot):
        bot, mock_client, _ = patched_bot
        mock_client.im.v1.chat.get.return_value = MagicMock(
            success=MagicMock(return_value=True)
        )
        bot.get_chat_info("oc_chat1")
        mock_client.im.v1.chat.get.assert_called_once()

    def test_get_chat_members(self, patched_bot):
        bot, mock_client, _ = patched_bot
        mock_client.im.v1.chat_members.get.return_value = MagicMock(
            success=MagicMock(return_value=True)
        )
        bot.get_chat_members("oc_chat1")
        mock_client.im.v1.chat_members.get.assert_called_once()

    def test_get_chat_members_with_page_token(self, patched_bot):
        bot, mock_client, _ = patched_bot
        mock_client.im.v1.chat_members.get.return_value = MagicMock(
            success=MagicMock(return_value=True)
        )
        bot.get_chat_members("oc_chat1", page_token="tok_abc")
        mock_client.im.v1.chat_members.get.assert_called_once()
