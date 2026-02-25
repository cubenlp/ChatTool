"""
Unit tests for ChatSession.
Uses a fake chat factory to avoid real LLM calls.
The mock mimics chattool.Chat's actual interface:
  - chat._chat_log  (list)
  - chat.system(text)
  - chat.user(text)
  - chat.ask(text) -> str
"""
import pytest
from unittest.mock import MagicMock, call

from chattool.tools.lark.session import ChatSession


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_session(system="你是助手", max_history=None, reply="AI 回复"):
    """Return a ChatSession backed by a mock Chat factory."""
    call_count = [0]

    def factory():
        call_count[0] += 1
        chat = MagicMock()
        chat._chat_log = [{"role": "system", "content": system}] if system else []
        chat.ask.return_value = reply
        return chat

    session = ChatSession(system=system, max_history=max_history, chat_factory=factory)
    session._call_count = call_count
    return session


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.lark
class TestChatSession:
    def test_chat_returns_ai_reply(self):
        s = make_session(reply="你好！")
        result = s.chat("user1", "嗨")
        assert result == "你好！"

    def test_ask_is_called_with_text(self):
        s = make_session()
        s.chat("user1", "问题内容")
        chat_obj = s._sessions["user1"]
        chat_obj.ask.assert_called_once_with("问题内容")

    def test_chat_creates_session_on_first_use(self):
        s = make_session()
        assert not s.has_session("user1")
        s.chat("user1", "消息")
        assert s.has_session("user1")

    def test_different_users_get_separate_sessions(self):
        s = make_session()
        s.chat("alice", "你好")
        s.chat("bob", "Hello")
        assert s.user_count() == 2

    def test_same_user_reuses_session(self):
        s = make_session()
        s.chat("alice", "第一条")
        s.chat("alice", "第二条")
        # Factory only called once
        assert s._call_count[0] == 1
        assert s.user_count() == 1

    def test_clear_removes_session(self):
        s = make_session()
        s.chat("user1", "消息")
        assert s.has_session("user1")
        s.clear("user1")
        assert not s.has_session("user1")

    def test_clear_nonexistent_user_is_safe(self):
        s = make_session()
        s.clear("ghost")  # must not raise

    def test_clear_all(self):
        s = make_session()
        s.chat("u1", "m")
        s.chat("u2", "m")
        s.chat("u3", "m")
        assert s.user_count() == 3
        s.clear_all()
        assert s.user_count() == 0

    def test_has_session_false_before_first_chat(self):
        s = make_session()
        assert not s.has_session("nobody")

    def test_has_session_true_after_chat(self):
        s = make_session()
        s.chat("someone", "hi")
        assert s.has_session("someone")

    def test_user_count_increments(self):
        s = make_session()
        assert s.user_count() == 0
        s.chat("u1", "m")
        assert s.user_count() == 1
        s.chat("u2", "m")
        assert s.user_count() == 2

    def test_user_count_decrements_after_clear(self):
        s = make_session()
        s.chat("u1", "m")
        s.chat("u2", "m")
        s.clear("u1")
        assert s.user_count() == 1

    def test_max_history_trims_log(self):
        """With max_history=1, only system(1) + 1 turn(2) = 3 messages kept."""
        chat = MagicMock()
        # Pre-populate with system + 4 messages (2 turns)
        chat._chat_log = [
            {"role": "system",    "content": "sys"},
            {"role": "user",      "content": "old1"},
            {"role": "assistant", "content": "rep1"},
            {"role": "user",      "content": "old2"},
            {"role": "assistant", "content": "rep2"},
        ]
        chat.ask.return_value = "new"

        s = ChatSession(max_history=1, chat_factory=lambda: chat)
        s.chat("u1", "新问题")

        # After trimming: system + 1 turn → max 3 messages
        assert len(chat._chat_log) <= 3

    def test_new_session_after_clear(self):
        """After clearing, the next chat starts a fresh factory-created session."""
        s = make_session()
        s.chat("u1", "hi")
        s.clear("u1")
        s.chat("u1", "hi again")
        assert s._call_count[0] == 2  # factory called twice
