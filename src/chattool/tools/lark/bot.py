import re
import json
import threading
from flask import Flask
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    import lark_oapi
    from lark_oapi.ws import Client as WSClient
    from lark_oapi.adapter.flask import parse_req, parse_resp
    from lark_oapi.api.im.v1 import (
        CreateMessageRequest, CreateMessageRequestBody,
        ReplyMessageRequest, ReplyMessageRequestBody,
        GetChatRequest, GetChatMembersRequest, 
        P2ImChatMemberBotAddedV1,
        )
    from lark_oapi.event.callback.model.p2_card_action_trigger import (
        P2CardActionTriggerResponse,
        )
except Exception as e:
    LarkBot = None

from chattool.config import FeishuConfig

from .elements import BaseMessage
from .context import MessageContext


class LarkBot:
    """
    Lark/Feishu Bot.

    Quick start (WebSocket, no public server needed)::

        bot = LarkBot()

        @bot.on_message
        def handle(ctx):
            ctx.reply(f"收到：{ctx.text}")

        bot.start()

    With LLM::
        sessions = {}

        @bot.command("/clear")
        def clear(ctx):
            sessions.pop(ctx.sender_id, None)
            ctx.reply("记忆已清除 ✅")

        @bot.on_message
        def chat(ctx):
            c = sessions.setdefault(ctx.sender_id, Chat(system="你是一个助手"))
            c.user(ctx.text)
            ctx.reply(c.assistant())

        bot.start()
    """

    def __init__(self, app_id:str=None, app_secret:str=None, api_base:str=None):
        app_id = app_id or FeishuConfig().FEISHU_APP_ID.value
        app_secret = app_secret or FeishuConfig().FEISHU_APP_SECRET.value
        api_base = api_base or FeishuConfig().FEISHU_API_BASE.value or "https://open.feishu.cn"
        assert app_id and app_secret, "Feishu App ID and App Secret are required"
        self.app_id = app_id
        self.app_secret = app_secret
        
        builder = (
            lark_oapi.Client.builder()
            .app_id(app_id)
            .app_secret(app_secret)
            .log_level(lark_oapi.LogLevel.INFO)
        )
        if api_base:
            builder.domain(api_base)
        self.client = builder.build()

        # Handler registry
        self._message_handlers: List[Tuple[Optional[Callable], Callable]] = []
        # matcher is None → fallback; otherwise a callable(ctx) → bool
        self._command_handlers: Dict[str, Callable] = {}
        self._card_handlers: Dict[str, Callable] = {}
        self._bot_added_handlers: List[Callable] = []

    # ------------------------------------------------------------------
    # Decorators
    # ------------------------------------------------------------------

    def on_message(
        self,
        func: Callable = None,
        *,
        group_only: bool = False,
        private_only: bool = False,
    ):
        """
        Register a fallback message handler.

        Can be used as a plain decorator or with keyword arguments::

            @bot.on_message
            def handle(ctx): ...

            @bot.on_message(group_only=True)
            def group_handler(ctx): ...
        """
        def decorator(f: Callable) -> Callable:
            def matcher(ctx: MessageContext) -> bool:
                if group_only and not ctx.is_group:
                    return False
                if private_only and ctx.is_group:
                    return False
                return True
            self._message_handlers.append((matcher, f))
            return f

        if func is not None:
            # Used as @bot.on_message without arguments
            return decorator(func)
        return decorator

    def command(self, cmd: str):
        """
        Register a handler for a slash command.

        The command string is matched against the beginning of the message
        text (case-insensitive, stripped)::

            @bot.command("/help")
            def on_help(ctx): ...
        """
        def decorator(f: Callable) -> Callable:
            self._command_handlers[cmd.lower().strip()] = f
            return f
        return decorator

    def regex(self, pattern: str, flags: int = 0):
        """
        Register a handler that fires when the message text matches *pattern*.
        The match object is stored as ``ctx._match`` so groups are accessible::

            @bot.regex(r"^查询\\s+(.+)$")
            def on_query(ctx):
                keyword = ctx._match.group(1)
                ctx.reply(f"查询：{keyword}")
        """
        compiled = re.compile(pattern, flags)

        def decorator(f: Callable) -> Callable:
            def matcher(ctx: MessageContext) -> bool:
                m = compiled.match(ctx.text)
                if m:
                    ctx._match = m  # type: ignore[attr-defined]
                    return True
                return False
            self._message_handlers.append((matcher, f))
            return f
        return decorator

    def card_action(self, action_key: str):
        """
        Register a handler for interactive card button callbacks.

        *action_key* is matched against ``ctx.action_value`` dict's ``"action"``
        field (or the entire value string if it is not a dict)::

            @bot.card_action("approve")
            def on_approve(ctx):
                ctx.update_card(Card("已通过").text("✅").build())
        """
        def decorator(f: Callable) -> Callable:
            self._card_handlers[action_key] = f
            return f
        return decorator

    def on_bot_added(self, func: Callable) -> Callable:
        """
        Register a handler called when the bot is added to a group.

            @bot.on_bot_added
            def welcome(chat_id):
                bot.send_text(chat_id, "chat_id", "大家好，我是 AI 助手！")
        """
        self._bot_added_handlers.append(func)
        return func

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def _dispatch_message(self, data: Any) -> None:
        ctx = MessageContext(self, data)
        text_stripped = ctx.text.strip()

        # 1. Try command handlers first
        for cmd, handler in self._command_handlers.items():
            if text_stripped.lower().startswith(cmd):
                try:
                    handler(ctx)
                except Exception as e:
                    lark_oapi.logger.error(f"[LarkBot] command handler error: {e}")
                return

        # 2. Try registered message handlers in order
        for matcher, handler in self._message_handlers:
            try:
                if matcher is None or matcher(ctx):
                    handler(ctx)
                    return
            except Exception as e:
                lark_oapi.logger.error(f"[LarkBot] message handler error: {e}")
                return

    def _dispatch_card_action(self, data: Any):
        """Handle P2CardActionTrigger events."""
        action_value = getattr(getattr(data.event, "action", None), "value", {})
        action_key = None
        if isinstance(action_value, dict):
            action_key = action_value.get("action")
        elif isinstance(action_value, str):
            action_key = action_value

        resp = P2CardActionTriggerResponse()
        handler = self._card_handlers.get(action_key) if action_key else None
        if handler:
            card_ctx = _CardActionContext(self, data)
            try:
                result = handler(card_ctx)
                if result is not None:
                    return result
                if card_ctx._updated_card is not None:
                    resp.card = card_ctx._updated_card
                if card_ctx._toast is not None:
                    resp.toast = card_ctx._toast
            except Exception as e:
                lark_oapi.logger.error(f"[LarkBot] card_action handler error: {e}")
        return resp

    # ------------------------------------------------------------------
    # Start
    # ------------------------------------------------------------------

    def _build_event_handler(
        self,
        encrypt_key: str = "",
        verification_token: str = "",
    ) -> lark_oapi.EventDispatcherHandler:
        builder = lark_oapi.EventDispatcherHandler.builder(
            encrypt_key,
            verification_token,
            lark_oapi.LogLevel.DEBUG,
        ).register_p2_im_message_receive_v1(self._dispatch_message)

        if self._card_handlers:
            builder = builder.register_p2_card_action_trigger(
                self._dispatch_card_action
            )

        if self._bot_added_handlers:
            def _on_bot_added(data: P2ImChatMemberBotAddedV1) -> None:
                chat_id = data.event.chat_id
                for h in self._bot_added_handlers:
                    try:
                        h(chat_id)
                    except Exception as e:
                        lark_oapi.logger.error(f"[LarkBot] on_bot_added error: {e}")

            builder = builder.register_p2_im_chat_member_bot_added_v1(_on_bot_added)

        return builder.build()

    def start(
        self,
        mode: str = "ws",
        encrypt_key: str = "",
        verification_token: str = "",
        host: str = "0.0.0.0",
        port: int = 7777,
        path: str = "/webhook/event",
    ) -> None:
        """
        Start the bot.

        Args:
            mode: ``"ws"`` (WebSocket long-polling, default) or
                  ``"flask"`` (HTTP Webhook via Flask).
            encrypt_key: Event encryption key (leave empty if not configured).
            verification_token: Verification token (leave empty if not configured).
            host: Host for Flask mode.
            port: Port for Flask mode.
            path: URL path for Flask mode.
        """
        if mode == "ws":
            self._start_ws(encrypt_key, verification_token)
        elif mode == "flask":
            self._start_flask(encrypt_key, verification_token, host, port, path)
        else:
            raise ValueError(f"Unknown mode: {mode!r}. Use 'ws' or 'flask'.")

    def start_background(
        self,
        mode: str = "ws",
        encrypt_key: str = "",
        verification_token: str = "",
        **kwargs,
    ) -> threading.Thread:
        """Start the bot in a background daemon thread and return it."""
        t = threading.Thread(
            target=self.start,
            kwargs=dict(
                mode=mode,
                encrypt_key=encrypt_key,
                verification_token=verification_token,
                **kwargs,
            ),
            daemon=True,
        )
        t.start()
        return t

    def _start_ws(self, encrypt_key: str, verification_token: str) -> None:
        event_handler = self._build_event_handler(encrypt_key, verification_token)
        ws = (
            WSClient.builder()
            .app_id(self.app_id)
            .app_secret(self.app_secret)
            .event_handler(event_handler)
            .build()
        )
        lark_oapi.logger.info("[LarkBot] Starting WebSocket connection...")
        ws.start()

    def _start_flask(
        self,
        encrypt_key: str,
        verification_token: str,
        host: str,
        port: int,
        path: str,
    ) -> None:
        event_handler = self._build_event_handler(encrypt_key, verification_token)
        app = Flask(__name__)

        @app.route(path, methods=["POST"])
        def webhook():
            resp = event_handler.do(parse_req())
            return parse_resp(resp)

        lark_oapi.logger.info(f"[LarkBot] Starting Flask webhook on {host}:{port}{path}")
        app.run(host=host, port=port)

    # ------------------------------------------------------------------
    # Send helpers
    # ------------------------------------------------------------------

    def _send_message(
        self,
        receive_id: str,
        receive_id_type: str,
        msg_type: str,
        content: str,
    ) -> Any:
        request_body = (
            CreateMessageRequestBody.builder()
            .receive_id(receive_id)
            .msg_type(msg_type)
            .content(content)
            .build()
        )
        request = (
            CreateMessageRequest.builder()
            .receive_id_type(receive_id_type)
            .request_body(request_body)
            .build()
        )
        response = self.client.im.v1.message.create(request)
        if not response.success():
            lark_oapi.logger.error(
                f"client.im.v1.message.create failed, "
                f"code: {response.code}, msg: {response.msg}, "
                f"log_id: {response.get_log_id()}"
            )
        return response

    def send_message(
        self, receive_id: str, receive_id_type: str, message: BaseMessage
    ) -> Any:
        """Send a BaseMessage object."""
        return self._send_message(
            receive_id, receive_id_type, message.msg_type, message.to_json()
        )

    def send_text(self, receive_id: str, receive_id_type: str, text: str) -> Any:
        """Send a plain-text message."""
        return self._send_message(
            receive_id, receive_id_type, "text", json.dumps({"text": text})
        )

    def send_post(self, receive_id: str, receive_id_type: str, content: dict) -> Any:
        """Send a rich-text (post) message."""
        return self._send_message(
            receive_id, receive_id_type, "post", json.dumps(content)
        )

    def send_image(self, receive_id: str, receive_id_type: str, image_key: str) -> Any:
        """Send an image message."""
        return self._send_message(
            receive_id, receive_id_type, "image", json.dumps({"image_key": image_key})
        )

    def send_card(
        self, receive_id: str, receive_id_type: str, card_content: dict
    ) -> Any:
        """Send an interactive card message."""
        return self._send_message(
            receive_id, receive_id_type, "interactive", json.dumps(card_content)
        )

    # ------------------------------------------------------------------
    # Reply helpers
    # ------------------------------------------------------------------

    def reply(self, message_id: str, text: str) -> Any:
        """Quote-reply to *message_id* with plain text."""
        return self._reply_message(message_id, "text", json.dumps({"text": text}))

    def reply_card(self, message_id: str, card: dict) -> Any:
        """Quote-reply to *message_id* with an interactive card."""
        return self._reply_message(message_id, "interactive", json.dumps(card))

    def _reply_message(self, message_id: str, msg_type: str, content: str) -> Any:
        request = (
            ReplyMessageRequest.builder()
            .message_id(message_id)
            .request_body(
                ReplyMessageRequestBody.builder()
                .content(content)
                .msg_type(msg_type)
                .build()
            )
            .build()
        )
        response = self.client.im.v1.message.reply(request)
        if not response.success():
            lark_oapi.logger.error(
                f"client.im.v1.message.reply failed, "
                f"code: {response.code}, msg: {response.msg}, "
                f"log_id: {response.get_log_id()}"
            )
        return response

    # ------------------------------------------------------------------
    # Group / Chat helpers
    # ------------------------------------------------------------------

    def get_chat_info(self, chat_id: str, user_id_type: str = "open_id") -> Any:
        """Get group/chat information."""
        request = (
            GetChatRequest.builder()
            .chat_id(chat_id)
            .user_id_type(user_id_type)
            .build()
        )
        response = self.client.im.v1.chat.get(request)
        if not response.success():
            lark_oapi.logger.error(
                f"client.im.v1.chat.get failed, "
                f"code: {response.code}, msg: {response.msg}"
            )
        return response

    def get_chat_members(
        self,
        chat_id: str,
        member_id_type: str = "open_id",
        page_size: int = 20,
        page_token: str = None,
    ) -> Any:
        """Get members of a group chat."""
        builder = (
            GetChatMembersRequest.builder()
            .chat_id(chat_id)
            .member_id_type(member_id_type)
            .page_size(page_size)
        )
        if page_token:
            builder.page_token(page_token)
        response = self.client.im.v1.chat_members.get(builder.build())
        if not response.success():
            lark_oapi.logger.error(
                f"client.im.v1.chat_members.get failed, "
                f"code: {response.code}, msg: {response.msg}"
            )
        return response

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    def get_event_dispatcher(
        self,
        encrypt_key: str = None,
        verification_token: str = None,
    ) -> lark_oapi.EventDispatcherHandler:
        """Return a raw EventDispatcherHandler builder for advanced use."""
        return lark_oapi.EventDispatcherHandler.builder(
            encrypt_key or "",
            verification_token or "",
        )

    def get_bot_info(self) -> Any:
        """Fetch basic bot information via Bot v3 API."""
        request = (
            lark_oapi.BaseRequest.builder()
            .http_method(lark_oapi.HttpMethod.GET)
            .uri("/open-apis/bot/v3/info")
            .token_types({lark_oapi.AccessTokenType.TENANT})
            .build()
        )
        return self.client.request(request)


# ---------------------------------------------------------------------------
# Card action context (lightweight, used inside card_action handlers)
# ---------------------------------------------------------------------------

class _CardActionContext:
    """Context passed to @bot.card_action handlers."""

    def __init__(self, bot: LarkBot, data: Any):
        self._bot = bot
        self._data = data
        self._updated_card: Optional[dict] = None
        self._toast: Optional[dict] = None

        event = data.event
        self.action_value: Any = getattr(getattr(event, "action", None), "value", {})
        self.operator_id: str = getattr(
            getattr(getattr(event, "operator", None), "open_id", None), "__str__", lambda: ""
        )()
        self.message_id: str = getattr(
            getattr(event, "context", None), "open_message_id", ""
        ) or ""

    def update_card(self, card: dict) -> None:
        """Update the card content in the response."""
        self._updated_card = card

    def toast(self, message: str, type: str = "success") -> None:
        """Show a toast notification to the user who clicked."""
        self._toast = {"type": type, "content": message}
