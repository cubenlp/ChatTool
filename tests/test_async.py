import openai_api_call, time
from openai_api_call import Chat, process_chats, num_tokens_from_messages
from openai_api_call.asynctool import async_chat_completion
openai_api_call.api_key="free-123"
openai_api_call.base_url = "https://api.wzhecnu.cn"

# langs = ["Python", "Julia", "C++", "C", "Java", "JavaScript", "C#", "Go", "R", "Ruby"]
langs = ["Python", "Julia", "C++"]
chatlogs = [
    [{"role": "user", "content": f"Print hello using {lang}"}] for lang in langs
]

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
    chkpoint = "test_async.jsonl"
    t = time.time()
    resp = async_chat_completion(chatlogs, chkpoint, clearfile=True, ncoroutines=3)
    assert all(resp)
    print(f"Time elapsed: {time.time() - t:.2f}s")

def test_normal_process():
    chkpoint = "test_nomal.jsonl"
    def data2chat(data):
        chat = Chat(data)
        chat.getresponse()
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
