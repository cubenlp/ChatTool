import responses
from openai_api_call import chat_completion

mock_resp = {
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

@responses.activate
def test_chat_completion():
    responses.add(responses.POST, 'https://api.openai.com/v1/chat/completions',
                  json=mock_resp, status=200)
    resp = chat_completion(apikey="sk-123", messages=[{"role": "user", "content": "hello"}], model="gpt-3.5-turbo")
    assert resp == mock_resp
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == 'https://api.openai.com/v1/chat/completions'
    assert responses.calls[0].response.text == '{"id": "chatcmpl-6wXDUIbYzNkmqSF9UnjPuKLP1hHls", "object": "chat.completion", "created": 1679408728, "model": "gpt-3.5-turbo-0301", "usage": {"prompt_tokens": 8, "completion_tokens": 10, "total_tokens": 18}, "choices": [{"message": {"role": "assistant", "content": "Hello, how can I assist you today?"}, "finish_reason": "stop", "index": 0}]}'
    