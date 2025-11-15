import os
import pytest

from chattool import Chat

def test_init_uses_env_defaults():
    chat = Chat()
    assert chat.api_key is not None
    assert chat.model is not None
    assert chat.config.api_base is not None


def test_basic_sync_flow(chat: Chat):
    chat.system("你是一个编程助手，请用简洁明了的方式回答。")
    chat.user("请计算 6 + 7")
    resp = chat.get_response(update_history=True)

    # 响应基本有效性
    assert resp.is_valid()
    assert resp.message is not None
    assert isinstance(resp.content, str)
    assert len(resp.content) > 0

    # 历史与状态
    assert chat.last_response == resp
    assert chat.chat_log[-1]["role"] == "assistant"


def test_ask_convenience():
    chat = Chat()
    answer = chat.ask("请用一句话问候我。")
    assert isinstance(answer, str) and len(answer) > 0
    assert chat.chat_log[-1]["role"] == "assistant"

    before = len(chat.chat_log)
    answer2 = chat.ask("再来一句，但不要记录历史。", update_history=False)
    assert isinstance(answer2, str) and len(answer2) > 0
    assert len(chat.chat_log) == before


@pytest.mark.asyncio
async def test_async_ask():
    chat = Chat()
    chat.system("你是一个编程助手。")
    result = await chat.async_ask("给我两个 Python 提示")
    assert isinstance(result, str) and len(result) > 0
    assert chat.chat_log[-1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_async_get_response():
    chat = Chat(messages=[{"role": "user", "content": "请把 'Chattool' 翻译成中文"}])
    resp = await chat.async_get_response(update_history=True)

    assert resp.is_valid()
    assert resp.message is not None
    assert isinstance(resp.content, str) and len(resp.content) > 0
    assert chat.chat_log[-1]["role"] == "assistant"


def test_message_helpers(chat: Chat):
    chat.clear()
    chat.system("系统提示").user("你好").assistant("你好，我是助手")
    assert [m["role"] for m in chat.chat_log] == ["system", "user", "assistant"]

    popped = chat.pop()
    assert popped["role"] == "assistant"
    assert len(chat.chat_log) == 2


def test_copy(chat: Chat):
    chat.clear()
    chat.user("原始用户消息")
    c2 = chat.copy()
    assert c2.chat_log == chat.chat_log
    c2.user("追加一条")
    assert len(c2.chat_log) == len(chat.chat_log) + 1


# 可选：流式响应（若后端不支持流式将跳过）
@pytest.mark.asyncio
async def test_async_stream_response_optional():
    chat = Chat(messages=[{"role": "user", "content": "用两句话描述 Python"}])
    aggregated = ""
    try:
        async for res in chat.async_get_response_stream(stream=True):
            if res.delta_content:
                aggregated += res.delta_content
    except Exception as e:
        pytest.skip(f"流式响应不可用: {e}")

    # 如果成功，则应累积到非空内容，并写入历史
    assert isinstance(aggregated, str)
    assert len(aggregated) > 0
    assert chat.chat_log[-1]["role"] == "assistant"