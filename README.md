> **中文文档移步[这里](README_zh_CN.md)。**

# Openai API call
[![PyPI version](https://img.shields.io/pypi/v/openai_api_call.svg)](https://pypi.python.org/pypi/openai_api_call)
[![Tests](https://github.com/RexWzh/openai_api_call/actions/workflows/test.yml/badge.svg)](https://github.com/RexWzh/openai_api_call/actions/workflows/test.yml/)
[![Documentation Status](https://img.shields.io/badge/docs-github_pages-blue.svg)](https://apicall.wzhecnu.cn)
[![Coverage](https://codecov.io/gh/RexWzh/openai_api_call/branch/master/graph/badge.svg)](https://codecov.io/gh/RexWzh/openai_api_call.jl)

<!-- 
[![Updates](https://pyup.io/repos/github/RexWzh/openai_api_call/shield.svg)](https://pyup.io/repos/github/RexWzh/openai_api_call/) 
-->

A simple wrapper for OpenAI API, which can be used to send requests and get responses.

## Installation

```bash
pip install openai-api-call --upgrade
```

## Usage

### Set API Key

```py
import openai_api_call as apicall
apicall.api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

Or set `OPENAI_API_KEY` in `~/.bashrc` to avoid setting the API key every time:

```bash
# Add the following code to ~/.bashrc
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

Also, you might set different `api_key` for each `Chat` object:

```py
from openai_api_call import Chat
chat = Chat("hello")
chat.api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### Set Proxy (Optional)

```py
from openai_api_call import proxy_on, proxy_off, proxy_status
# Check the current proxy
proxy_status()

# Set proxy(example)
proxy_on(http="127.0.0.1:7890", https="127.0.0.1:7890")

# Check the updated proxy
proxy_status()

# Turn off proxy
proxy_off() 
```

Alternatively, you can use a proxy URL to send requests from restricted network, as shown below:

```py
from openai_api_call import request

# set request url
request.base_url = "https://api.example.com"
```

### Basic Usage

Example 1, send prompt and return response:

```python
from openai_api_call import Chat, show_apikey

# Check if API key is set
show_apikey()

# Check if proxy is enabled
proxy_status()

# Send prompt and return response
chat = Chat("Hello, GPT-3.5!")
resp = chat.getresponse(update=False) # Not update the chat history, default to True
```

Example 2, customize the message template and return the information and the number of consumed tokens:

```python
import openai_api_call as apicall

# Customize the sending template
apicall.default_prompt = lambda msg: [
    {"role": "system", "content": "帮我翻译这段文字"},
    {"role": "user", "content": msg}
]
chat = Chat("Hello!")
# Set the number of retries to Inf
# The timeout for each request is 10 seconds
response = chat.getresponse(temperature=0.5, max_requests=-1, timeout=10)
print("Number of consumed tokens: ", response.total_tokens)
print("Returned content: ", response.content)

# Reset the default template
apicall.default_prompt = None
```

Example 3, continue chatting based on the last response:

```python
# first call
chat = Chat("Hello, GPT-3.5!")
resp = chat.getresponse() # update chat history, default is True
print(resp.content)

# continue chatting
chat.user("How are you?")
next_resp = chat.getresponse()
print(next_resp.content)

# fake response
chat.user("What's your name?")
chat.assistant("My name is GPT-3.5.")

# get the last result
print(chat[-1])

# save chat history
chat.save("chat_history.log", mode="w") # default to "a"

# print chat history
chat.print_log()
```

Moreover, you can check the usage status of the API key:

```py
# show usage status of the default API key
chat = Chat()
chat.show_usage_status()

# show usage status of the specified API key
chat.api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
chat.show_usage_status()
```

## License

This package is licensed under the MIT license. See the LICENSE file for more details.

## update log

- Since version `0.2.0`, `Chat` type is used to handle data
- Since version `0.3.0`, you can use different API Key to send requests.