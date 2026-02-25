import json
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from chattool.tools.lark.bot import LarkBot


class MessageContext:
    """
    Wraps an incoming P2ImMessageReceiveV1 event and provides
    convenience accessors and reply helpers.
    """

    def __init__(self, bot: "LarkBot", event_data: Any):
        self._bot = bot
        self._data = event_data
        self._event = event_data.event
        self._message = self._event.message
        self._sender = self._event.sender

        # Parse text content eagerly so ctx.text always works.
        self._text: str = ""
        if self._message.message_type == "text":
            try:
                self._text = json.loads(self._message.content).get("text", "")
            except (json.JSONDecodeError, AttributeError):
                pass

    # ------------------------------------------------------------------
    # Core accessors
    # ------------------------------------------------------------------

    @property
    def text(self) -> str:
        """Plain text of the message. Empty string for non-text messages."""
        return self._text

    @property
    def msg_type(self) -> str:
        """Message type: text / image / file / interactive / post / ..."""
        return self._message.message_type

    @property
    def message_id(self) -> str:
        """The unique message ID (om_xxx), used for reply/reaction/pin."""
        return self._message.message_id

    @property
    def chat_id(self) -> str:
        """Chat ID of the conversation (group chat_id or user open_id for p2p)."""
        return self._message.chat_id

    @property
    def chat_type(self) -> str:
        """'group' for group chat, 'p2p' for direct message."""
        return self._message.chat_type

    @property
    def is_group(self) -> bool:
        """True if the message was sent in a group chat."""
        return self.chat_type == "group"

    @property
    def sender_id(self) -> str:
        """Open ID of the message sender."""
        return self._sender.sender_id.open_id

    @property
    def sender_type(self) -> str:
        """'user' or 'bot'."""
        return self._sender.sender_type

    @property
    def thread_id(self) -> Optional[str]:
        """Thread (话题) ID if the message is inside a thread, else None."""
        return getattr(self._message, "thread_id", None) or None

    @property
    def raw(self) -> Any:
        """The original P2ImMessageReceiveV1 event object."""
        return self._data

    # ------------------------------------------------------------------
    # Reply helpers
    # ------------------------------------------------------------------

    def reply(self, text: str) -> Any:
        """Quote-reply to this message with plain text."""
        return self._bot.reply(self.message_id, text)

    def reply_card(self, card: Dict[str, Any]) -> Any:
        """Quote-reply to this message with an interactive card."""
        return self._bot.reply_card(self.message_id, card)

    def send(self, text: str) -> Any:
        """
        Send a new plain-text message to the same conversation
        (no quote, uses chat_id).
        """
        return self._bot.send_text(self.chat_id, "chat_id", text)

    def send_card(self, card: Dict[str, Any]) -> Any:
        """Send a card to the same conversation (no quote)."""
        return self._bot.send_card(self.chat_id, "chat_id", card)

    # ------------------------------------------------------------------
    # Content helpers
    # ------------------------------------------------------------------

    def get_content(self) -> Any:
        """
        Return parsed message content.
        - text    → str
        - image   → {"image_key": "..."}
        - file    → {"file_key": "..."}
        - post    → full post dict
        - other   → raw JSON dict
        """
        try:
            return json.loads(self._message.content)
        except (json.JSONDecodeError, AttributeError):
            return None

    def __repr__(self) -> str:
        return (
            f"<MessageContext msg_type={self.msg_type!r} "
            f"sender={self.sender_id!r} chat={self.chat_id!r} "
            f"text={self.text!r}>"
        )
