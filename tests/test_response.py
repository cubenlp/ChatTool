
# test for error response
from openai_api_call import Resp, default_prompt

err_api_key_resp = {
    "error": {
        "message": "Incorrect API key provided: sk-132. You can find your API key at https://platform.openai.com/account/api-keys.",
        "type": "invalid_request_error",
        "param": None,
        "code": "invalid_api_key"
    }
}

def test_error_message():
    resp = Resp(response=err_api_key_resp)
    assert resp.error_message == "Incorrect API key provided: sk-132. You can find your API key at https://platform.openai.com/account/api-keys."
    assert resp.error_type == "invalid_request_error"
    assert resp.error_param == None
    assert resp.error_code == "invalid_api_key"

def test_is_valid():
    resp = Resp(response=err_api_key_resp)
    assert resp.is_valid() == False

# test for valid response

valid_response = {
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

def test_usage():
    resp = Resp(response=valid_response)
    assert resp.total_tokens == 18
    assert resp.prompt_tokens == 8
    assert resp.completion_tokens == 10

def test_content():
    resp = Resp(response=valid_response)
    assert resp.content == "Hello, how can I assist you today?"

def test_valid():
    resp = Resp(response=valid_response)
    assert resp.id == "chatcmpl-6wXDUIbYzNkmqSF9UnjPuKLP1hHls"
    assert resp.model == "gpt-3.5-turbo-0301"
    assert resp.created == 1679408728
    assert resp.is_valid() == True

# test next talk
def test_next_talk():
    resp = Resp(response=valid_response)
    msg = "hello!"
    resp._request_msg = default_prompt(msg)
    new_prompt = resp.next_prompt("How are you?")
    assert new_prompt == [
        {'role': 'user', 'content': 'hello!'},
        {'role': 'assistant', 'content': 'Hello, how can I assist you today?'},
        {'role': 'user', 'content': 'How are you?'}
    ]
    