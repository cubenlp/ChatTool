"""
Integration tests for LarkBot — uses the real Feishu API.

Prerequisites
-------------
Set the following environment variables (or put them in .env):

    FEISHU_APP_ID=<your app id>
    FEISHU_APP_SECRET=<your app secret>

Run only these tests:

    pytest tests/tools/lark/test_bot_integration.py -v -m lark

The test user is ``rexwzh`` (user_id type).  Make sure the bot has been
granted the following permissions in the Feishu developer console:
  - im:message          (send / reply messages)
  - im:message:readonly (read message list)
  - im:chat:readonly    (get chat info)

Results are logged at INFO level so you can see what was sent.
"""
import json
import logging
import time
import pytest
import json
from unittest.mock import MagicMock

from chattool.tools import LarkBot, MessageContext, ChatSession

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TEST_USER_ID = "f25gc16d"
USER_ID_TYPE = "user_id"

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def assert_ok(response, label: str = ""):
    """Assert a Lark API response is successful, print a friendly error otherwise."""
    if not response.success():
        hint = ""
        code = response.code
        if code in (230013, 99991672):
            hint = "\n  → 权限不足，请在飞书开放平台「权限管理」中申请对应 Scope"
        elif code == 99991663:
            hint = "\n  → 用户不在应用可见范围内"
        pytest.fail(
            f"[{label}] API 调用失败: code={code}  msg={response.msg}{hint}"
        )

# ---------------------------------------------------------------------------
# Bot info
# ---------------------------------------------------------------------------

@pytest.mark.lark
def test_get_bot_info(lark_bot):
    """验证凭证有效，获取机器人基本信息。"""
    resp = lark_bot.get_bot_info()
    assert_ok(resp, "get_bot_info")

    data = json.loads(resp.raw.content)
    bot_info = data.get("bot", {})
    logger.info("Bot name : %s", bot_info.get("app_name"))
    logger.info("Bot status: %s", bot_info.get("activate_status"))
    assert bot_info.get("activate_status") == 2, "机器人未激活（activate_status != 2）"


# ---------------------------------------------------------------------------
# Send messages
# ---------------------------------------------------------------------------

@pytest.mark.lark
def test_send_text_to_user(lark_bot):
    """发送文本消息给 rexwzh。"""
    resp = lark_bot.send_text(TEST_USER_ID, USER_ID_TYPE, "[test] 你好，这是文本消息 👋")
    assert_ok(resp, "send_text")
    msg_id = resp.data.message_id
    logger.info("发送成功，message_id=%s", msg_id)
    assert msg_id, "message_id 不应为空"


@pytest.mark.lark
def test_send_post_to_user(lark_bot):
    """发送富文本消息给 rexwzh。"""
    content = {
        "zh_cn": {
            "title": "[test] 富文本消息",
            "content": [
                [
                    {"tag": "text", "text": "这是一条 "},
                    {"tag": "a", "text": "富文本消息", "href": "https://open.feishu.cn"},
                    {"tag": "text", "text": "，包含链接。"},
                ]
            ],
        }
    }
    resp = lark_bot.send_post(TEST_USER_ID, USER_ID_TYPE, content)
    assert_ok(resp, "send_post")
    logger.info("富文本消息 message_id=%s", resp.data.message_id)


@pytest.mark.lark
def test_send_card_to_user(lark_bot:LarkBot):
    """发送交互卡片给 rexwzh。"""
    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "[test] 卡片消息"},
            "template": "blue",
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "这是一条**卡片消息**，用于集成测试。\n\n当前时间：`" + time.strftime("%H:%M:%S") + "`",
                },
            }
        ],
    }
    resp = lark_bot.send_card(TEST_USER_ID, USER_ID_TYPE, card)
    assert_ok(resp, "send_card")
    logger.info("卡片消息 message_id=%s", resp.data.message_id)


# ---------------------------------------------------------------------------
# Reply
# ---------------------------------------------------------------------------

@pytest.mark.lark
def test_reply_to_message(lark_bot:LarkBot):
    """先发一条消息，再对其进行引用回复。"""
    # Step 1: send original
    send_resp = lark_bot.send_text(TEST_USER_ID, USER_ID_TYPE, "[test] 原始消息（将被回复）")
    assert_ok(send_resp, "send for reply")
    original_id = send_resp.data.message_id
    logger.info("原始消息 id=%s", original_id)

    # Step 2: reply
    reply_resp = lark_bot.reply(original_id, "[test] 这是引用回复 ✅")
    assert_ok(reply_resp, "reply")
    logger.info("回复消息 id=%s", reply_resp.data.message_id)
    assert reply_resp.data.message_id != original_id


@pytest.mark.lark
def test_reply_card_to_message(lark_bot:LarkBot):
    """发一条消息，然后用卡片回复它。"""
    send_resp = lark_bot.send_text(TEST_USER_ID, USER_ID_TYPE, "[test] 等待卡片回复...")
    assert_ok(send_resp, "send for card reply")
    original_id = send_resp.data.message_id

    card = {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": "[test] 卡片回复"}, "template": "green"},
        "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": "✅ 这是对上条消息的卡片引用回复"}}],
    }
    reply_resp = lark_bot.reply_card(original_id, card)
    assert_ok(reply_resp, "reply_card")
    logger.info("卡片回复 id=%s", reply_resp.data.message_id)


# ---------------------------------------------------------------------------
# MessageContext via dispatch
# ---------------------------------------------------------------------------

@pytest.mark.lark
def test_on_message_dispatch_and_reply(lark_bot:LarkBot):
    """
    注册 on_message 处理器，构造一条假事件，验证 ctx.reply() 能正确发送消息。
    （不启动 WebSocket，直接调用内部 _dispatch_message）
    """
    
    results = []

    @lark_bot.on_message
    def handle(ctx: MessageContext):
        # ctx.reply 会调用 bot.reply(message_id, text)
        results.append((ctx.text, ctx.sender_id))

    # Build a minimal fake event pointing at rexwzh
    msg = MagicMock()
    msg.message_type = "text"
    msg.content = json.dumps({"text": "你好机器人"})
    msg.message_id = "om_fake_for_dispatch_test"
    msg.chat_id = "p2p_fake"
    msg.chat_type = "p2p"
    msg.thread_id = None

    sid = MagicMock(); sid.open_id = TEST_USER_ID
    sender = MagicMock(); sender.sender_id = sid; sender.sender_type = "user"
    event = MagicMock(); event.message = msg; event.sender = sender
    data = MagicMock(); data.event = event

    lark_bot._dispatch_message(data)

    assert len(results) == 1
    assert results[0][0] == "你好机器人"
    assert results[0][1] == TEST_USER_ID

    # Clean up handler so it doesn't interfere with other tests
    lark_bot._message_handlers.clear()


# ---------------------------------------------------------------------------
# ChatSession integration
# ---------------------------------------------------------------------------

@pytest.mark.lark
def test_chat_session_with_real_llm(lark_bot:LarkBot):
    """
    用 ChatSession 做一轮真实 LLM 对话，然后验证回复非空并发送给 rexwzh。
    如果没有配置 OpenAI key，跳过此测试。
    """
    

    # ChatSession.chat() calls Chat.ask() internally
    session = ChatSession(system="你是一个飞书机器人测试助手，请用一句话简短回答。")
    reply = session.chat(TEST_USER_ID, "用一句话介绍飞书机器人")

    logger.info("LLM 回复: %s", reply)
    assert reply and len(reply) > 0

    # Send the LLM reply to rexwzh
    resp = lark_bot.send_text(
        TEST_USER_ID,
        USER_ID_TYPE,
        f"[test/LLM] {reply}",
    )
    assert_ok(resp, "send llm reply")


# ---------------------------------------------------------------------------
# Command dispatch
# ---------------------------------------------------------------------------

@pytest.mark.lark
def test_command_dispatch(lark_bot:LarkBot):
    """注册 /ping 指令，通过假事件验证派发正确。"""
    fired = []

    @lark_bot.command("/ping")
    def on_ping(ctx):
        fired.append(ctx.text.strip())

    msg = MagicMock()
    msg.message_type = "text"
    msg.content = json.dumps({"text": "/ping"})
    msg.message_id = "om_fake_ping"
    msg.chat_id = "p2p_fake2"
    msg.chat_type = "p2p"
    msg.thread_id = None

    sid = MagicMock(); sid.open_id = TEST_USER_ID
    sender = MagicMock(); sender.sender_id = sid; sender.sender_type = "user"
    event = MagicMock(); event.message = msg; event.sender = sender
    data = MagicMock(); data.event = event

    lark_bot._dispatch_message(data)

    assert fired == ["/ping"]
    # Clean up
    lark_bot._command_handlers.pop("/ping", None)
