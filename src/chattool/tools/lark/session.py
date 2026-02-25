"""
ChatSession: per-user LLM conversation session manager.

Integrates with chattool.Chat so each Feishu user gets an independent
conversation history. No external dependencies beyond chattool itself.

Usage::

    from chattool.tools.lark.session import ChatSession

    session = ChatSession(system="你是一个工作助手")

    @bot.command("/clear")
    def clear(ctx):
        session.clear(ctx.sender_id)
        ctx.reply("记忆已清除 ✅")

    @bot.on_message
    def handle(ctx):
        reply = session.chat(ctx.sender_id, ctx.text)
        ctx.reply(reply)
"""

from typing import Callable, Dict, Optional


class ChatSession:
    """
    Per-user conversation session manager backed by chattool.Chat.

    Each user identified by ``user_id`` gets an independent ``Chat`` instance
    so conversation history is never shared between users.

    Args:
        system: System prompt shared by all users.
        max_history: Maximum number of dialogue *turns* to retain per user
                     (one turn = one user message + one assistant reply).
                     ``None`` means unlimited.
        chat_factory: Optional callable that returns a new ``Chat`` instance.
                      Defaults to ``lambda: Chat(system=system)``.
    """

    def __init__(
        self,
        system: str = "",
        max_history: Optional[int] = None,
        chat_factory: Optional[Callable] = None,
    ):
        self.system = system
        self.max_history = max_history
        self._sessions: Dict[str, object] = {}

        if chat_factory is not None:
            self._factory = chat_factory
        else:
            self._factory = self._default_factory

    def _default_factory(self):
        from chattool import Chat  # lazy import

        c = Chat()
        if self.system:
            c.system(self.system)
        return c

    def _get_or_create(self, user_id: str):
        if user_id not in self._sessions:
            self._sessions[user_id] = self._factory()
        return self._sessions[user_id]

    def _trim_history(self, chat) -> None:
        """Trim the internal chat log to at most ``max_history`` turns."""
        if self.max_history is None:
            return
        log = chat._chat_log
        # system message (index 0) is never removed
        # one turn = 2 messages (user + assistant)
        max_msgs = 1 + self.max_history * 2
        if len(log) > max_msgs:
            chat._chat_log = log[:1] + log[-(max_msgs - 1):]

    def chat(self, user_id: str, text: str) -> str:
        """
        Send *text* to the user's conversation and return the assistant reply.

        Creates a new session for the user if one does not exist yet.
        Uses ``Chat.ask()`` which handles the full user → API → assistant cycle.
        """
        c = self._get_or_create(user_id)
        self._trim_history(c)
        # ask() = user() + get_response() + return content string
        return c.ask(text)

    def clear(self, user_id: str) -> None:
        """Delete the conversation history for *user_id*."""
        self._sessions.pop(user_id, None)

    def clear_all(self) -> None:
        """Delete conversation histories for all users."""
        self._sessions.clear()

    def user_count(self) -> int:
        """Return the number of active user sessions."""
        return len(self._sessions)

    def has_session(self, user_id: str) -> bool:
        """Return True if *user_id* has an active session."""
        return user_id in self._sessions
