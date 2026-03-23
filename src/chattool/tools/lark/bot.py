import re
import json
import threading
from types import SimpleNamespace
from uuid import uuid4
from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask
    import lark_oapi
    from lark_oapi.event.callback.model.p2_card_action_trigger import P2CardActionTriggerResponse
    from lark_oapi.api.im.v1 import P2ImChatMemberBotAddedV1

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
        app_id = app_id or FeishuConfig.FEISHU_APP_ID.value
        app_secret = app_secret or FeishuConfig.FEISHU_APP_SECRET.value
        api_base = api_base or FeishuConfig.FEISHU_API_BASE.value or "https://open.feishu.cn"
        assert app_id and app_secret, "Feishu App ID and App Secret are required"
        self.app_id = app_id
        self.app_secret = app_secret

        import lark_oapi
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
                    import lark_oapi
                    lark_oapi.logger.error(f"[LarkBot] command handler error: {e}")
                return

        # 2. Try registered message handlers in order
        for matcher, handler in self._message_handlers:
            try:
                if matcher is None or matcher(ctx):
                    handler(ctx)
                    return
            except Exception as e:
                import lark_oapi
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
        
        from lark_oapi.event.callback.model.p2_card_action_trigger import P2CardActionTriggerResponse
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
                import lark_oapi
                lark_oapi.logger.error(f"[LarkBot] card_action handler error: {e}")
        return resp

    # ------------------------------------------------------------------
    # Start
    # ------------------------------------------------------------------

    def _build_event_handler(
        self,
        encrypt_key: str = "",
        verification_token: str = "",
    ) -> 'lark_oapi.EventDispatcherHandler':
        import lark_oapi
        from lark_oapi.api.im.v1 import P2ImChatMemberBotAddedV1
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
        log_level: str = "INFO",
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
            log_level: ``"DEBUG"`` / ``"INFO"`` / ``"WARN"`` / ``"ERROR"``.
        """
        import lark_oapi
        _LOG_LEVEL_MAP = {
            "DEBUG": lark_oapi.LogLevel.DEBUG,
            "INFO": lark_oapi.LogLevel.INFO,
            "WARNING": lark_oapi.LogLevel.WARNING,
            "ERROR": lark_oapi.LogLevel.ERROR,
        }
        level = _LOG_LEVEL_MAP.get(log_level.upper(), lark_oapi.LogLevel.INFO)
        lark_oapi.logger.setLevel(level.value)
        if mode == "ws":
            self._start_ws(encrypt_key, verification_token, level)
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

    def _start_ws(
        self,
        encrypt_key: str,
        verification_token: str,
        level: 'lark_oapi.LogLevel' = None, # type: ignore
    ) -> None:
        if level is None:
            import lark_oapi
            level = lark_oapi.LogLevel.INFO
            
        event_handler = self._build_event_handler(encrypt_key, verification_token)
        import lark_oapi
        from lark_oapi.ws import Client as WSClient
        ws = WSClient(
            app_id=self.app_id,
            app_secret=self.app_secret,
            event_handler=event_handler,
            log_level=level,
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
        from flask import Flask
        import lark_oapi
        from lark_oapi.adapter.flask import parse_req, parse_resp
        
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
        import lark_oapi
        from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody
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
        """Send an image message by image_key."""
        return self._send_message(
            receive_id, receive_id_type, "image", json.dumps({"image_key": image_key})
        )

    def upload_image(self, path: str, image_type: str = "message") -> Any:
        """Upload an image file and return the response (use resp.data.image_key)."""
        import lark_oapi
        from lark_oapi.api.im.v1 import CreateImageRequest, CreateImageRequestBody
        with open(path, "rb") as f:
            request = (
                CreateImageRequest.builder()
                .request_body(
                    CreateImageRequestBody.builder()
                    .image_type(image_type)
                    .image(f)
                    .build()
                ).build()
            )
            response = self.client.im.v1.image.create(request)
        if not response.success():
            lark_oapi.logger.error(
                f"im.v1.image.create failed, "
                f"code: {response.code}, msg: {response.msg}"
            )
        return response

    def send_image_file(
        self, receive_id: str, receive_id_type: str, path: str
    ) -> Any:
        """Upload a local image and send it in one step."""
        upload_resp = self.upload_image(path)
        if not upload_resp.success():
            return upload_resp
        return self.send_image(receive_id, receive_id_type, upload_resp.data.image_key)

    def upload_file(
        self, path: str, file_type: str = "stream", file_name: str = None
    ) -> Any:
        """Upload a file and return the response (use resp.data.file_key)."""
        import os
        import lark_oapi
        from lark_oapi.api.im.v1 import CreateFileRequest, CreateFileRequestBody
        if file_name is None:
            file_name = os.path.basename(path)
        with open(path, "rb") as f:
            request = (
                CreateFileRequest.builder()
                .request_body(
                    CreateFileRequestBody.builder()
                    .file_type(file_type)
                    .file_name(file_name)
                    .file(f)
                    .build()
                ).build()
            )
            response = self.client.im.v1.file.create(request)
        if not response.success():
            lark_oapi.logger.error(
                f"im.v1.file.create failed, "
                f"code: {response.code}, msg: {response.msg}"
            )
        return response

    def send_file(
        self, receive_id: str, receive_id_type: str, path: str,
        file_type: str = "stream",
    ) -> Any:
        """Upload a local file and send it in one step."""
        upload_resp = self.upload_file(path, file_type=file_type)
        if not upload_resp.success():
            return upload_resp
        return self._send_message(
            receive_id, receive_id_type, "file",
            json.dumps({"file_key": upload_resp.data.file_key}),
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
        import lark_oapi
        from lark_oapi.api.im.v1 import ReplyMessageRequest, ReplyMessageRequestBody
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
        import lark_oapi
        from lark_oapi.api.im.v1 import GetChatRequest
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
        import lark_oapi
        from lark_oapi.api.im.v1 import GetChatMembersRequest
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
    ) -> 'lark_oapi.EventDispatcherHandler':
        """Return a raw EventDispatcherHandler builder for advanced use."""
        import lark_oapi
        return lark_oapi.EventDispatcherHandler.builder(
            encrypt_key or "",
            verification_token or "",
        )

    def get_bot_info(self) -> Any:
        """Fetch basic bot information via Bot v3 API."""
        import lark_oapi
        request = (
            lark_oapi.BaseRequest.builder()
            .http_method(lark_oapi.HttpMethod.GET)
            .uri("/open-apis/bot/v3/info")
            .token_types({lark_oapi.AccessTokenType.TENANT})
            .build()
        )
        return self.client.request(request)

    def get_scopes(self) -> Any:
        """List all scopes (permissions) of this app and their grant status."""
        from lark_oapi.api.application.v6 import ListScopeRequest
        request = ListScopeRequest.builder().build()
        return self.client.application.v6.scope.list(request)

    # ------------------------------------------------------------------
    # Bitable helpers
    # ------------------------------------------------------------------

    def create_bitable_app(
        self,
        name: str,
        folder_token: str = None,
        time_zone: str = None,
    ) -> Any:
        """Create a Bitable app."""
        from lark_oapi.api.bitable.v1 import CreateAppRequest, ReqApp

        payload = {"name": name}
        if folder_token:
            payload["folder_token"] = folder_token
        if time_zone:
            payload["time_zone"] = time_zone

        request = CreateAppRequest.builder().request_body(ReqApp(payload)).build()
        return self.client.bitable.v1.app.create(request)

    def list_bitable_tables(
        self,
        app_token: str,
        page_size: int = 100,
        page_token: str = None,
    ) -> Any:
        """List tables in a Bitable app."""
        from lark_oapi.api.bitable.v1 import ListAppTableRequest

        builder = ListAppTableRequest.builder().app_token(app_token).page_size(page_size)
        if page_token:
            builder.page_token(page_token)
        return self.client.bitable.v1.app_table.list(builder.build())

    def create_bitable_table(
        self,
        app_token: str,
        name: str,
        default_view_name: str = None,
        fields: List[dict] = None,
    ) -> Any:
        """Create a table in a Bitable app."""
        from lark_oapi.api.bitable.v1 import (
            CreateAppTableRequest,
            CreateAppTableRequestBody,
            ReqTable,
        )

        table_payload = {"name": name}
        if default_view_name:
            table_payload["default_view_name"] = default_view_name
        if fields:
            table_payload["fields"] = fields

        request = (
            CreateAppTableRequest.builder()
            .app_token(app_token)
            .request_body(
                CreateAppTableRequestBody.builder()
                .table(ReqTable(table_payload))
                .build()
            )
            .build()
        )
        return self.client.bitable.v1.app_table.create(request)

    def list_bitable_fields(
        self,
        app_token: str,
        table_id: str,
        page_size: int = 100,
        page_token: str = None,
    ) -> Any:
        """List fields in a Bitable table."""
        from lark_oapi.api.bitable.v1 import ListAppTableFieldRequest

        builder = (
            ListAppTableFieldRequest.builder()
            .app_token(app_token)
            .table_id(table_id)
            .page_size(page_size)
        )
        if page_token:
            builder.page_token(page_token)
        return self.client.bitable.v1.app_table_field.list(builder.build())

    def create_bitable_field(
        self,
        app_token: str,
        table_id: str,
        field_name: str,
        field_type: int,
        property: dict = None,
        description: dict = None,
        ui_type: str = None,
        is_primary: bool = None,
        is_hidden: bool = None,
    ) -> Any:
        """Create a field in a Bitable table."""
        from lark_oapi.api.bitable.v1 import CreateAppTableFieldRequest, AppTableField

        payload = {
            "field_name": field_name,
            "type": field_type,
        }
        if property is not None:
            payload["property"] = property
        if description is not None:
            payload["description"] = description
        if ui_type is not None:
            payload["ui_type"] = ui_type
        if is_primary is not None:
            payload["is_primary"] = is_primary
        if is_hidden is not None:
            payload["is_hidden"] = is_hidden

        request = (
            CreateAppTableFieldRequest.builder()
            .app_token(app_token)
            .table_id(table_id)
            .client_token(str(uuid4()))
            .request_body(AppTableField(payload))
            .build()
        )
        return self.client.bitable.v1.app_table_field.create(request)

    def list_bitable_records(
        self,
        app_token: str,
        table_id: str,
        page_size: int = 100,
        page_token: str = None,
        user_id_type: str = "user_id",
    ) -> Any:
        """List records in a Bitable table."""
        from lark_oapi.api.bitable.v1 import ListAppTableRecordRequest

        builder = (
            ListAppTableRecordRequest.builder()
            .app_token(app_token)
            .table_id(table_id)
            .page_size(page_size)
            .user_id_type(user_id_type)
        )
        if page_token:
            builder.page_token(page_token)
        return self.client.bitable.v1.app_table_record.list(builder.build())

    def create_bitable_record(
        self,
        app_token: str,
        table_id: str,
        fields: Dict[str, Any],
        user_id_type: str = "user_id",
    ) -> Any:
        """Create a record in a Bitable table."""
        from lark_oapi.api.bitable.v1 import CreateAppTableRecordRequest, AppTableRecord

        request = (
            CreateAppTableRecordRequest.builder()
            .app_token(app_token)
            .table_id(table_id)
            .user_id_type(user_id_type)
            .client_token(str(uuid4()))
            .request_body(AppTableRecord({"fields": fields}))
            .build()
        )
        return self.client.bitable.v1.app_table_record.create(request)

    def batch_create_bitable_records(
        self,
        app_token: str,
        table_id: str,
        records: List[Dict[str, Any]],
        user_id_type: str = "user_id",
    ) -> Any:
        """Batch-create records in a Bitable table."""
        from lark_oapi.api.bitable.v1 import (
            AppTableRecord,
            BatchCreateAppTableRecordRequest,
            BatchCreateAppTableRecordRequestBody,
        )

        request_records = [AppTableRecord({"fields": item}) for item in records]
        request = (
            BatchCreateAppTableRecordRequest.builder()
            .app_token(app_token)
            .table_id(table_id)
            .user_id_type(user_id_type)
            .client_token(str(uuid4()))
            .request_body(
                BatchCreateAppTableRecordRequestBody.builder()
                .records(request_records)
                .build()
            )
            .build()
        )
        return self.client.bitable.v1.app_table_record.batch_create(request)

    # ------------------------------------------------------------------
    # Calendar helpers
    # ------------------------------------------------------------------

    def list_calendars(
        self,
        page_size: int = 50,
        page_token: str = None,
    ) -> Any:
        """List accessible calendars."""
        from lark_oapi.api.calendar.v4 import ListCalendarRequest

        builder = ListCalendarRequest.builder().page_size(page_size)
        if page_token:
            builder.page_token(page_token)
        return self.client.calendar.v4.calendar.list(builder.build())

    def get_primary_calendar(self, user_id_type: str = "user_id") -> Any:
        """Fetch the primary calendar for the current user/bot context."""
        from lark_oapi.api.calendar.v4 import PrimaryCalendarRequest

        request = PrimaryCalendarRequest.builder().user_id_type(user_id_type).build()
        return self.client.calendar.v4.calendar.primary(request)

    def create_calendar_event(
        self,
        calendar_id: str,
        summary: str,
        start_time: Dict[str, str],
        end_time: Dict[str, str],
        description: str = None,
        need_notification: bool = None,
        user_id_type: str = "user_id",
    ) -> Any:
        """Create a calendar event."""
        from lark_oapi.api.calendar.v4 import CreateCalendarEventRequest, CalendarEvent

        payload = {
            "summary": summary,
            "start_time": start_time,
            "end_time": end_time,
        }
        if description:
            payload["description"] = description
        if need_notification is not None:
            payload["need_notification"] = need_notification

        request = (
            CreateCalendarEventRequest.builder()
            .calendar_id(calendar_id)
            .user_id_type(user_id_type)
            .idempotency_key(str(uuid4()))
            .request_body(CalendarEvent(payload))
            .build()
        )
        return self.client.calendar.v4.calendar_event.create(request)

    def list_calendar_events(
        self,
        calendar_id: str,
        start_time: str,
        end_time: str,
        page_size: int = 50,
        page_token: str = None,
        user_id_type: str = "user_id",
    ) -> Any:
        """List events in a time range."""
        from lark_oapi.api.calendar.v4 import ListCalendarEventRequest

        builder = (
            ListCalendarEventRequest.builder()
            .calendar_id(calendar_id)
            .start_time(start_time)
            .end_time(end_time)
            .page_size(page_size)
            .user_id_type(user_id_type)
        )
        if page_token:
            builder.page_token(page_token)
        return self.client.calendar.v4.calendar_event.list(builder.build())

    def get_calendar_event(
        self,
        calendar_id: str,
        event_id: str,
        user_id_type: str = "user_id",
    ) -> Any:
        """Get a calendar event."""
        from lark_oapi.api.calendar.v4 import GetCalendarEventRequest

        request = (
            GetCalendarEventRequest.builder()
            .calendar_id(calendar_id)
            .event_id(event_id)
            .user_id_type(user_id_type)
            .build()
        )
        return self.client.calendar.v4.calendar_event.get(request)

    def patch_calendar_event(
        self,
        calendar_id: str,
        event_id: str,
        summary: str = None,
        start_time: Dict[str, str] = None,
        end_time: Dict[str, str] = None,
        description: str = None,
        need_notification: bool = None,
        user_id_type: str = "user_id",
    ) -> Any:
        """Patch a calendar event."""
        from lark_oapi.api.calendar.v4 import PatchCalendarEventRequest, CalendarEvent

        payload: Dict[str, Any] = {}
        if summary is not None:
            payload["summary"] = summary
        if start_time is not None:
            payload["start_time"] = start_time
        if end_time is not None:
            payload["end_time"] = end_time
        if description is not None:
            payload["description"] = description
        if need_notification is not None:
            payload["need_notification"] = need_notification

        request = (
            PatchCalendarEventRequest.builder()
            .calendar_id(calendar_id)
            .event_id(event_id)
            .user_id_type(user_id_type)
            .request_body(CalendarEvent(payload))
            .build()
        )
        return self.client.calendar.v4.calendar_event.patch(request)

    def reply_calendar_event(
        self,
        calendar_id: str,
        event_id: str,
        rsvp_status: str,
    ) -> Any:
        """Reply to a calendar invite."""
        from lark_oapi.api.calendar.v4 import (
            ReplyCalendarEventRequest,
            ReplyCalendarEventRequestBody,
        )

        request = (
            ReplyCalendarEventRequest.builder()
            .calendar_id(calendar_id)
            .event_id(event_id)
            .request_body(
                ReplyCalendarEventRequestBody.builder()
                .rsvp_status(rsvp_status)
                .build()
            )
            .build()
        )
        return self.client.calendar.v4.calendar_event.reply(request)

    def list_freebusy(
        self,
        time_min: str,
        time_max: str,
        user_ids: List[str] = None,
        room_ids: List[str] = None,
        include_external_calendar: bool = False,
        only_busy: bool = False,
        need_rsvp_status: bool = False,
        user_id_type: str = "user_id",
    ) -> Any:
        """List freebusy information."""
        from lark_oapi.api.calendar.v4 import ListFreebusyRequest, ListFreebusyRequestBody

        body_builder = (
            ListFreebusyRequestBody.builder()
            .time_min(time_min)
            .time_max(time_max)
            .include_external_calendar(include_external_calendar)
            .only_busy(only_busy)
            .need_rsvp_status(need_rsvp_status)
        )
        if user_ids:
            body_builder.user_id(user_ids)
        if room_ids:
            body_builder.room_id(room_ids)

        request = (
            ListFreebusyRequest.builder()
            .user_id_type(user_id_type)
            .request_body(body_builder.build())
            .build()
        )
        return self.client.calendar.v4.freebusy.list(request)

    # ------------------------------------------------------------------
    # Task helpers
    # ------------------------------------------------------------------

    def create_task(
        self,
        summary: str,
        description: str = None,
        due_timestamp: int = None,
        due_is_all_day: bool = False,
        members: List[Dict[str, Any]] = None,
        user_id_type: str = "user_id",
    ) -> Any:
        """Create a task."""
        from lark_oapi.api.task.v2 import CreateTaskRequest, InputTask

        payload: Dict[str, Any] = {"summary": summary}
        if description:
            payload["description"] = description
        if due_timestamp is not None:
            payload["due"] = {
                "timestamp": due_timestamp,
                "is_all_day": due_is_all_day,
            }
        if members:
            payload["members"] = members

        request = (
            CreateTaskRequest.builder()
            .user_id_type(user_id_type)
            .request_body(InputTask(payload))
            .build()
        )
        return self.client.task.v2.task.create(request)

    def list_tasks(
        self,
        completed: bool = None,
        page_size: int = 50,
        page_token: str = None,
        user_id_type: str = "user_id",
    ) -> Any:
        """List tasks."""
        from lark_oapi.api.task.v2 import ListTaskRequest

        builder = (
            ListTaskRequest.builder()
            .page_size(page_size)
            .user_id_type(user_id_type)
        )
        if completed is not None:
            builder.completed(completed)
        if page_token:
            builder.page_token(page_token)
        return self.client.task.v2.task.list(builder.build())

    def get_task(self, task_guid: str, user_id_type: str = "user_id") -> Any:
        """Get a task."""
        from lark_oapi.api.task.v2 import GetTaskRequest

        request = (
            GetTaskRequest.builder()
            .task_guid(task_guid)
            .user_id_type(user_id_type)
            .build()
        )
        return self.client.task.v2.task.get(request)

    def patch_task(
        self,
        task_guid: str,
        summary: str = None,
        description: str = None,
        completed_at: int = None,
        due_timestamp: int = None,
        due_is_all_day: bool = False,
        user_id_type: str = "user_id",
    ) -> Any:
        """Patch a task."""
        from lark_oapi.api.task.v2 import PatchTaskRequest, PatchTaskRequestBody, InputTask

        payload: Dict[str, Any] = {}
        update_fields: List[str] = []

        if summary is not None:
            payload["summary"] = summary
            update_fields.append("summary")
        if description is not None:
            payload["description"] = description
            update_fields.append("description")
        if completed_at is not None:
            payload["completed_at"] = completed_at
            update_fields.append("completed_at")
        if due_timestamp is not None:
            payload["due"] = {
                "timestamp": due_timestamp,
                "is_all_day": due_is_all_day,
            }
            update_fields.append("due")

        request = (
            PatchTaskRequest.builder()
            .task_guid(task_guid)
            .user_id_type(user_id_type)
            .request_body(
                PatchTaskRequestBody.builder()
                .task(InputTask(payload))
                .update_fields(update_fields)
                .build()
            )
            .build()
        )
        return self.client.task.v2.task.patch(request)

    def create_tasklist(
        self,
        name: str,
        members: List[Dict[str, Any]] = None,
        user_id_type: str = "user_id",
    ) -> Any:
        """Create a tasklist."""
        from lark_oapi.api.task.v2 import CreateTasklistRequest, InputTasklist

        payload: Dict[str, Any] = {"name": name}
        if members:
            payload["members"] = members

        request = (
            CreateTasklistRequest.builder()
            .user_id_type(user_id_type)
            .request_body(InputTasklist(payload))
            .build()
        )
        return self.client.task.v2.tasklist.create(request)

    def list_tasklists(
        self,
        page_size: int = 50,
        page_token: str = None,
        user_id_type: str = "user_id",
    ) -> Any:
        """List tasklists."""
        from lark_oapi.api.task.v2 import ListTasklistRequest

        builder = (
            ListTasklistRequest.builder()
            .page_size(page_size)
            .user_id_type(user_id_type)
        )
        if page_token:
            builder.page_token(page_token)
        return self.client.task.v2.tasklist.list(builder.build())

    def get_tasklist(self, tasklist_guid: str, user_id_type: str = "user_id") -> Any:
        """Get a tasklist."""
        from lark_oapi.api.task.v2 import GetTasklistRequest

        request = (
            GetTasklistRequest.builder()
            .tasklist_guid(tasklist_guid)
            .user_id_type(user_id_type)
            .build()
        )
        return self.client.task.v2.tasklist.get(request)

    def list_tasklist_tasks(
        self,
        tasklist_guid: str,
        completed: bool = None,
        page_size: int = 50,
        page_token: str = None,
        user_id_type: str = "user_id",
    ) -> Any:
        """List tasks under a tasklist."""
        from lark_oapi.api.task.v2 import TasksTasklistRequest

        builder = (
            TasksTasklistRequest.builder()
            .tasklist_guid(tasklist_guid)
            .page_size(page_size)
            .user_id_type(user_id_type)
        )
        if completed is not None:
            builder.completed(completed)
        if page_token:
            builder.page_token(page_token)
        return self.client.task.v2.tasklist.tasks(builder.build())

    def add_tasklist_members(
        self,
        tasklist_guid: str,
        members: List[Dict[str, Any]],
        user_id_type: str = "user_id",
    ) -> Any:
        """Add members to a tasklist."""
        from lark_oapi.api.task.v2 import (
            AddMembersTasklistRequest,
            AddMembersTasklistRequestBody,
        )

        request = (
            AddMembersTasklistRequest.builder()
            .tasklist_guid(tasklist_guid)
            .user_id_type(user_id_type)
            .request_body(
                AddMembersTasklistRequestBody.builder()
                .members(members)
                .build()
            )
            .build()
        )
        return self.client.task.v2.tasklist.add_members(request)

    # ------------------------------------------------------------------
    # IM read helpers
    # ------------------------------------------------------------------

    def list_messages(
        self,
        container_id: str,
        container_id_type: str = "chat",
        start_time: str = None,
        end_time: str = None,
        sort_type: str = None,
        page_size: int = 20,
        page_token: str = None,
    ) -> Any:
        """List IM messages in a chat container."""
        from lark_oapi.api.im.v1 import ListMessageRequest

        builder = (
            ListMessageRequest.builder()
            .container_id_type(container_id_type)
            .container_id(container_id)
            .page_size(page_size)
        )
        if start_time:
            builder.start_time(start_time)
        if end_time:
            builder.end_time(end_time)
        if sort_type:
            builder.sort_type(sort_type)
        if page_token:
            builder.page_token(page_token)
        return self.client.im.v1.message.list(builder.build())

    def get_message(self, message_id: str) -> Any:
        """Get a single IM message."""
        from lark_oapi.api.im.v1 import GetMessageRequest

        request = GetMessageRequest.builder().message_id(message_id).build()
        return self.client.im.v1.message.get(request)

    def get_message_resource(
        self,
        message_id: str,
        file_key: str,
        resource_type: str,
    ) -> Any:
        """Fetch a binary resource from a message."""
        from lark_oapi.api.im.v1 import GetMessageResourceRequest

        request = (
            GetMessageResourceRequest.builder()
            .message_id(message_id)
            .file_key(file_key)
            .type(resource_type)
            .build()
        )
        return self.client.im.v1.message_resource.get(request)

    # ------------------------------------------------------------------
    # Docs / Docx helpers
    # ------------------------------------------------------------------

    def create_doc_document(self, title: str, folder_token: str = None) -> Any:
        """Create a Feishu docx document."""
        from lark_oapi.api.docx.v1 import CreateDocumentRequest, CreateDocumentRequestBody

        body_builder = CreateDocumentRequestBody.builder().title(title)
        if folder_token:
            body_builder.folder_token(folder_token)

        request = (
            CreateDocumentRequest.builder()
            .request_body(body_builder.build())
            .build()
        )
        return self.client.docx.v1.document.create(request)

    def get_doc_document(self, document_id: str) -> Any:
        """Fetch Feishu docx document metadata."""
        from lark_oapi.api.docx.v1 import GetDocumentRequest

        request = GetDocumentRequest.builder().document_id(document_id).build()
        return self.client.docx.v1.document.get(request)

    def get_doc_raw_content(self, document_id: str, lang: int = None) -> Any:
        """Fetch Feishu docx raw text content."""
        from lark_oapi.api.docx.v1 import RawContentDocumentRequest

        builder = RawContentDocumentRequest.builder().document_id(document_id)
        if lang is not None:
            builder.lang(lang)

        return self.client.docx.v1.document.raw_content(builder.build())

    def get_doc_block_children(
        self,
        document_id: str,
        block_id: str,
        page_size: int = None,
        page_token: str = None,
        with_descendants: bool = False,
    ) -> Any:
        """List child blocks under a specific block."""
        from lark_oapi.api.docx.v1 import GetDocumentBlockChildrenRequest

        builder = (
            GetDocumentBlockChildrenRequest.builder()
            .document_id(document_id)
            .block_id(block_id)
        )
        if page_size is not None:
            builder.page_size(page_size)
        if page_token:
            builder.page_token(page_token)
        if with_descendants:
            builder.with_descendants(True)

        return self.client.docx.v1.document_block_children.get(builder.build())

    def append_doc_texts(
        self,
        document_id: str,
        texts: List[str],
        block_id: str = None,
        index: int = None,
    ) -> Any:
        """Append plain text paragraph blocks to a Feishu docx document."""
        from lark_oapi.api.docx.v1 import (
            CreateDocumentBlockChildrenRequest,
            CreateDocumentBlockChildrenRequestBody,
            Block,
            Text,
            TextElement,
            TextRun,
        )

        paragraphs = []
        for text in texts:
            text_run = TextRun.builder().content(text).build()
            text_element = TextElement.builder().text_run(text_run).build()
            text_block = Text.builder().elements([text_element]).build()
            paragraphs.append(Block.builder().block_type(2).text(text_block).build())

        body_builder = (
            CreateDocumentBlockChildrenRequestBody.builder()
            .children(paragraphs)
        )
        if index is not None:
            body_builder.index(index)

        request = (
            CreateDocumentBlockChildrenRequest.builder()
            .document_id(document_id)
            .block_id(block_id or document_id)
            .client_token(str(uuid4()))
            .request_body(body_builder.build())
            .build()
        )
        return self.client.docx.v1.document_block_children.create(request)

    def append_doc_blocks(
        self,
        document_id: str,
        blocks: List[dict],
        block_id: str = None,
        index: int = None,
    ) -> Any:
        """Append structured docx blocks to a Feishu docx document."""
        from lark_oapi.api.docx.v1 import (
            Block,
            CreateDocumentBlockChildrenRequest,
            CreateDocumentBlockChildrenRequestBody,
        )

        normalized_blocks = []
        for block in blocks:
            block_data = dict(block)
            for key in ["block_id", "parent_id", "children", "comment_ids"]:
                block_data.pop(key, None)
            code_payload = block_data.get("code")
            if isinstance(code_payload, dict):
                code_payload = dict(code_payload)
                style_payload = code_payload.get("style")
                if isinstance(style_payload, dict):
                    style_payload = dict(style_payload)
                    language = style_payload.get("language")
                    if isinstance(language, str):
                        normalized_language = language.strip()
                        if normalized_language.isdigit():
                            style_payload["language"] = int(normalized_language)
                        else:
                            style_payload.pop("language", None)
                    if style_payload:
                        code_payload["style"] = style_payload
                    else:
                        code_payload.pop("style", None)
                block_data["code"] = code_payload
            normalized_blocks.append(Block(block_data))

        body_builder = (
            CreateDocumentBlockChildrenRequestBody.builder()
            .children(normalized_blocks)
        )
        if index is not None:
            body_builder.index(index)

        request = (
            CreateDocumentBlockChildrenRequest.builder()
            .document_id(document_id)
            .block_id(block_id or document_id)
            .client_token(str(uuid4()))
            .request_body(body_builder.build())
            .build()
        )
        return self.client.docx.v1.document_block_children.create(request)

    def append_doc_blocks_safe(
        self,
        document_id: str,
        blocks: List[dict],
        block_id: str = None,
        index: int = None,
        batch_size: int = 20,
    ) -> Any:
        """Append structured blocks in small batches."""
        normalized = [block for block in blocks if isinstance(block, dict)]
        if not normalized:
            return SimpleNamespace(
                code=0,
                msg="ok",
                data=SimpleNamespace(document_revision_id=None, children=[]),
                success=lambda: True,
            )

        if batch_size <= 0:
            batch_size = 1

        all_children = []
        revision_id = None
        for offset in range(0, len(normalized), batch_size):
            chunk = normalized[offset: offset + batch_size]
            resp = self.append_doc_blocks(
                document_id=document_id,
                blocks=chunk,
                block_id=block_id,
                index=index,
            )
            if getattr(resp, "code", 0) != 0:
                return resp
            revision_id = getattr(resp.data, "document_revision_id", revision_id)
            all_children.extend(getattr(resp.data, "children", None) or [])

        return SimpleNamespace(
            code=0,
            msg="ok",
            data=SimpleNamespace(document_revision_id=revision_id, children=all_children),
            success=lambda: True,
        )

    def append_doc_texts_safe(
        self,
        document_id: str,
        texts: List[str],
        block_id: str = None,
        index: int = None,
        batch_size: int = 20,
    ) -> Any:
        """Append text paragraphs in small batches, with single-paragraph fallback."""
        normalized = [text for text in texts if text and text.strip()]
        if not normalized:
            return SimpleNamespace(
                code=0,
                msg="ok",
                data=SimpleNamespace(document_revision_id=None, children=[]),
                success=lambda: True,
            )

        if batch_size <= 0:
            batch_size = 1

        all_children = []
        revision_id = None

        for offset in range(0, len(normalized), batch_size):
            chunk = normalized[offset: offset + batch_size]
            resp = self.append_doc_texts(
                document_id=document_id,
                texts=chunk,
                block_id=block_id,
                index=index,
            )
            if getattr(resp, "code", 0) == 0:
                revision_id = getattr(resp.data, "document_revision_id", revision_id)
                all_children.extend(getattr(resp.data, "children", None) or [])
                continue

            for text in chunk:
                single_resp = self.append_doc_text(
                    document_id=document_id,
                    text=text,
                    block_id=block_id,
                    index=index,
                )
                if getattr(single_resp, "code", 0) != 0:
                    return single_resp
                revision_id = getattr(single_resp.data, "document_revision_id", revision_id)
                all_children.extend(getattr(single_resp.data, "children", None) or [])

        return SimpleNamespace(
            code=0,
            msg="ok",
            data=SimpleNamespace(document_revision_id=revision_id, children=all_children),
            success=lambda: True,
        )

    def append_doc_text(
        self,
        document_id: str,
        text: str,
        block_id: str = None,
        index: int = None,
    ) -> Any:
        """Append a single plain text paragraph block to a Feishu docx document."""
        return self.append_doc_texts(
            document_id=document_id,
            texts=[text],
            block_id=block_id,
            index=index,
        )

    def get_doc_meta(self, document_id: str, with_url: bool = True) -> Any:
        """Fetch Drive metadata for a docx document."""
        from lark_oapi.api.drive.v1 import BatchQueryMetaRequest, MetaRequest, RequestDoc

        request_doc = (
            RequestDoc.builder()
            .doc_token(document_id)
            .doc_type("docx")
            .build()
        )
        body = (
            MetaRequest.builder()
            .request_docs([request_doc])
            .with_url(with_url)
            .build()
        )
        request = BatchQueryMetaRequest.builder().request_body(body).build()
        return self.client.drive.v1.meta.batch_query(request)


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
