import chattool, time, os
from chattool import Chat, process_chats, num_tokens_from_messages
from chattool.asynctool import async_chat_completion
import asyncio, pytest

# langs = ["Python", "Julia", "C++", "C", "Java", "JavaScript", "C#", "Go", "R", "Ruby"]
langs = ["Python", "Julia", "C++"]
chatlogs = [
    [{"role": "user", "content": f"Print hello using {lang}"}] for lang in langs
]
testpath = 'tests/testfiles/'

def test_apikey():
    assert chattool.api_key.startswith("sk-")

def test_base_url():
    assert chattool.base_url.startswith("http")

def test_stream():
    chat = Chat("hello")
    async def show_resp(chat):
        async for resp in chat.async_stream_responses():
            print(resp.delta_content, end='')
    asyncio.run(show_resp(chat))

def test_async_typewriter():
    def typewriter_effect(text, delay):
        for char in text:
            print(char, end='', flush=True)
            time.sleep(delay)
    async def show_resp(chat):
        async for resp in chat.async_stream_responses():
            typewriter_effect(resp.delta_content, 0.02)
    chat = Chat("Print hello using Python")
    asyncio.run(show_resp(chat))

def test_async_process():
    chkpoint = testpath + "test_async.jsonl"
    t = time.time()
    resp = async_chat_completion(chatlogs[:1], chkpoint, clearfile=True, ncoroutines=3)
    resp = async_chat_completion(chatlogs, chkpoint, clearfile=True, ncoroutines=3)
    assert all(resp)
    print(f"Time elapsed: {time.time() - t:.2f}s")

def test_async_process_withfunc():
    chkpoint = testpath + "test_async_withfunc.jsonl"
    words = ["hello", "Can you help me?", "Do not translate this word", "I need help with my homework"]
    def msg2log(msg):
        chat = Chat()
        chat.system("translate the words from English to Chinese")
        chat.user(msg)
        return chat.chat_log
    def max_tokens(chatlog):
        return Chat(chatlog).prompt_token()
    async_chat_completion(words, chkpoint, clearfile=True, ncoroutines=3, max_tokens=max_tokens, msg2log=msg2log)

def test_normal_process():
    chkpoint = testpath + "test_nomal.jsonl"
    def data2chat(data):
        chat = Chat(data)
        chat.getresponse(max_requests=3)
        return chat
    t = time.time()
    process_chats(chatlogs, data2chat, chkpoint, clearfile=True)
    print(f"Time elapsed: {time.time() - t:.2f}s")

def test_tokencounter():
    message = [{"role": "user", "content": "hello world!"}]
    prompttoken = num_tokens_from_messages(message)
    chat = Chat(message)
    resp = chat.getresponse()
    assert resp.prompt_tokens == prompttoken
