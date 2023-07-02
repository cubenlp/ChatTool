import responses, json
from openai_api_call import chat_completion, usage_status, debug_log, Chat
from openai_api_call.request import normalize_url, is_valid_url, valid_models
import openai_api_call

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

# test for valid models response
with open("tests/assets/model_response.json", "r") as f:
    valid_models_response = json.load(f)

@responses.activate
def test_valid_models():
    openai_api_call.api_key = "sk-123"
    responses.add(responses.GET, 'https://api.openai.com/v1/models',
                    json=valid_models_response, status=200)
    models = valid_models(api_key="sk-123", gpt_only=False)
    assert len(models) == 53
    models = valid_models(api_key="sk-123", gpt_only=True)
    assert len(models) == 5
    assert models == ['gpt-3.5-turbo-0613', 'gpt-3.5-turbo', 
                      'gpt-3.5-turbo-0301', 'gpt-3.5-turbo-16k-0613', 'gpt-3.5-turbo-16k']

@responses.activate
def test_debug_log():
    """Test the debug log"""
    responses.add(responses.GET, 'https://api.openai.com/v1/models',
                    json=valid_models_response, status=200)
    responses.add(responses.GET, 'https://api.openai.com/v1/dashboard/billing/subscription',
                    json=mock_usage, status=200)
    responses.add(responses.GET, 'https://api.openai.com/v1/dashboard/billing/usage',
                    json=mock_billing, status=200)
    responses.add(responses.POST, 'https://api.openai.com/v1/chat/completions',
                  json=mock_resp, status=200)
    responses.add(responses.GET, 'https://www.google.com', status=200)
    assert debug_log(net_url="https://www.google.com")
    assert not debug_log(net_url="https://baidu123.com") # invalid url

# test for function call
function_response = {
  "id": "chatcmpl-7X2vF57BKsEuzaSen0wFSI30Y2mJX",
  "object": "chat.completion",
  "created": 1688110413,
  "model": "gpt-3.5-turbo-0613",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": None,
        "function_call": {
          "name": "get_current_weather",
          "arguments": "{\n  \"location\": \"Boston, MA\"\n}"
        }
      },
      "finish_reason": "function_call"
    }
  ],
  "usage": {
    "prompt_tokens": 88,
    "completion_tokens": 18,
    "total_tokens": 106
  }
}

functions = [{
    "name": "get_current_weather",
    "description": "Get the current weather",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city and state, e.g. San Francisco, CA",
            },
            "format": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "The temperature unit to use. Infer this from the users location.",
            },
        },
        "required": ["location", "format"],
    },
}]

@responses.activate
def test_functions():
    responses.add(responses.POST, 'https://api.openai.com/v1/chat/completions',
                  json=function_response, status=200)
    chat = Chat("What is the weather in Boston?")
    chat.functions = functions
    resp = chat.getresponse()
    assert resp.finish_reason == "function_call"
    assert resp.function_call['name'] == "get_current_weather"
    assert resp.function_call['arguments'] == "{\n  \"location\": \"Boston, MA\"\n}"

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

def get_current_weather(location, unit="fahrenheit"):
    """Get the current weather in a given location"""
    weather_info = {
        "location": location,
        "temperature": "72",
        "unit": unit,
        "forecast": ["sunny", "windy"],
    }
    return json.dumps(weather_info)

@responses.activate
def test_run_conversation():
    """test case from openai"""
    responses.add(responses.POST, 'https://api.openai.com/v1/chat/completions',
                  json=function_response, status=200)
    # send the conversation and available functions to GPT
    messages = [{"role": "user", "content": "What's the weather like in Boston?"}]
    chat = Chat(messages)
    chat.functions = functions
    response = chat.getresponse()
    if response.is_function_call():
        # call the function
        available_functions = {
            "get_current_weather": get_current_weather,
        }
        function_name = response.function_call['name']
        fuction_to_call = available_functions[function_name]
        function_args = response.get_func_args()
        function_result = fuction_to_call(**function_args)
        # Step 4: send the info on the function call and function response to GPT
        chat.function(function_name, function_result)
        response = chat.getresponse()
        chat.print_log()
    
    ## use Chat object directly
    chat = Chat()
    chat.user("What's the weather like in Boston?")
    chat.functions = functions
    chat.function_call = 'auto'
    chat.available_functions = {
        "get_current_weather": get_current_weather,
    }
    chat.getresponse(update=True, funceval=True)
    
    