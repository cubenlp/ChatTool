import responses
from openai_api_call import chat_completion, usage_status
from openai_api_call.request import normalize_url, is_valid_url

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
    resp = chat_completion(api_key="sk-123", messages=[{"role": "user", "content": "hello"}], model="gpt-3.5-turbo")
    assert resp == mock_resp
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == 'https://api.openai.com/v1/chat/completions'
    assert responses.calls[0].response.text == '{"id": "chatcmpl-6wXDUIbYzNkmqSF9UnjPuKLP1hHls", "object": "chat.completion", "created": 1679408728, "model": "gpt-3.5-turbo-0301", "usage": {"prompt_tokens": 8, "completion_tokens": 10, "total_tokens": 18}, "choices": [{"message": {"role": "assistant", "content": "Hello, how can I assist you today?"}, "finish_reason": "stop", "index": 0}]}'

# test for usage status
mock_usage = {
  "object": "billing_subscription",
  "has_payment_method": False,
  "canceled": False,
  "canceled_at": None,
  "delinquent": None,
  "access_until": 1690848000,
  "soft_limit": 66667,
  "hard_limit": 83334,
  "system_hard_limit": 83334,
  "soft_limit_usd": 4.00002,
  "hard_limit_usd": 5.00004,
  "system_hard_limit_usd": 5.00004,
  "plan": {
    "title": "Explore",
    "id": "free"
  },
  "account_name": "apafa renor",
  "po_number": None,
  "billing_email": None,
  "tax_ids": None,
  "billing_address": None,
  "business_address": None
}

mock_billing = {
  "object": "list",
  "daily_costs": [
    {
      "timestamp": 1681171200.0,
      "line_items": [
        {
          "name": "Instruct models",
          "cost": 0.0
        },
        {
          "name": "Chat models",
          "cost": 106.619
        },
        {
          "name": "GPT-4",
          "cost": 0.0
        },
        {
          "name": "Fine-tuned models",
          "cost": 0.0
        },
        {
          "name": "Embedding models",
          "cost": 0.0
        },
        {
          "name": "Image models",
          "cost": 0.0
        },
        {
          "name": "Audio models",
          "cost": 0.0
        }
      ]
    }
  ],
  "total_usage": 106.619
}

@responses.activate
def test_usage_status():
    responses.add(responses.GET, 'https://api.openai.com/v1/dashboard/billing/subscription',
                    json=mock_usage, status=200)
    responses.add(responses.GET, 'https://api.openai.com/v1/dashboard/billing/usage',
                    json=mock_billing, status=200)
    storage, usage, daily = usage_status(api_key="sk-123")
    assert storage == 5.00004
    assert usage == 106.619 / 100
    assert len(daily) == 1
    assert daily[0]["timestamp"] == 1681171200.0
    assert sum([item["cost"] for item in daily[0]["line_items"]]) == 106.619

# normalize base url
def test_is_valid_url():
    assert is_valid_url("http://api.wzhecnu.cn") == True
    assert is_valid_url("https://www.google.com/") == True
    assert is_valid_url("ftp://ftp.debian.org/debian/") == True
    assert is_valid_url("api.wzhecnu.cn") == False
    assert is_valid_url("example.com") == False


def test_normalize_url():
    assert normalize_url("http://api.wzhecnu.cn/") == "http://api.wzhecnu.cn/"
    assert normalize_url("https://www.google.com") == "https://www.google.com"
    assert normalize_url("ftp://ftp.debian.org/debian/dists/stable/main/installer-amd64/current/images/cdrom/boot.img.gz") == "ftp://ftp.debian.org/debian/dists/stable/main/installer-amd64/current/images/cdrom/boot.img.gz"
    assert normalize_url("api.wzhecnu.cn") == "https://api.wzhecnu.cn"
    assert normalize_url("example.com/foo/bar") == "https://example.com/foo/bar"
