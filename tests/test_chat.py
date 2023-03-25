
from openai_api_call import Chat, Resp

## Test for the class `Chat`
response = {
    "id":"chatcmpl-6wXDUIbYzNkmqSF9UnjPuKLP1hHls",
    "object":"chat.completion",
    "created":1679408728,
    "model":"gpt-3.5-turbo-0301",
    "usage":{
        "prompt_tokens":8,
        "completion_tokens":10,
        "total_tokens":18
    },
    "choices":[
        {
            "message":{
                "role":"assistant",
                "content":"Hello, how can I assist you today?"
            },
            "finish_reason":"stop",
            "index":0
        }
    ]
}

def test_chat():
    chat = Chat(None)
    chat.user("Hi")
    chat.assistant("Hello, how can I assist you today?")
    chat.print_log()
    assert len(chat) == 2
    assert chat.pop() == {
        "role": "assistant",
        "content": "Hello, how can I assist you today?"
    }
    chat.clear()
    assert len(chat) == 0
    assert chat.history == []
    chat.user("Hi")
    chat.assistant("Hello, how can I assist you today?")
    chat.print_log()
    assert chat.history == [
        {
            "role": "user",
            "content": "Hi"
        },
        {
            "role": "assistant",
            "content": "Hello, how can I assist you today?"
        }
    ]
    chat.clear()
    chat.user("Hi")
    chat.assistant("Hello, how can I assist you today?")
    assert chat.copy().history == [
        {
            "role": "user",
            "content": "Hi"
        },
        {
            "role": "assistant",
            "content": "Hello, how can I assist you today?"
        }
    ]
    assert chat.history == [
        {
            "role": "user",
            "content": "Hi"
        },
        {
            "role": "assistant",
            "content": "Hello, how can I assist you today?"
        }
    ]
    chat.clear()
    chat.user("Hi")
    chat.assistant("Hello, how can I assist you today?")
    chat.print_log()
    assert chat.history == [
        {
            "role": "user",
            "content": "Hi"
        },
        {
            "role": "assistant",
            "content": "Hello, how can I assist you today?"
        }
    ]

## Test for the `Chat` with `Resp`

def test_chat_resp():
    chat = Chat(None)
    resp = Resp(response)
    chat.user("Hi")
    chat.assistant(resp.content)
    chat.print_log()
    assert len(chat) == 2
    assert chat.pop() == {
        "role": "assistant",
        "content": "Hello, how can I assist you today?"
    }
    chat.clear()
    chat.user("Hi")
    resp = Resp(response, chat)
    resp.chat.history == [
        {
            "role": "user",
            "content": "Hi"
        },
        {
            "role": "assistant",
            "content": "Hello, how can I assist you today?"
        }
    ]
    assert len(resp.chat) == 2
    