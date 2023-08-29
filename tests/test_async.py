import openai_api_call, time
from openai_api_call import Chat, process_chats
from openai_api_call.asynctool import async_chat_completion
openai_api_call.api_key="free-123"
openai_api_call.base_url = "https://api.wzhecnu.cn"


# langs = ["Python", "Julia", "C++", "C", "Java", "JavaScript", "C#", "Go", "R", "Ruby"]
langs = ["Python", "Julia", "C++"]
chatlogs = [
    [{"role": "user", "content": f"Print hello using {lang}"}] for lang in langs
]

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

test_async_process()