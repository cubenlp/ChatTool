> **中文文档移步[这里](README_zh_CN.md)。**

# Openai API call
[![PyPI version](https://img.shields.io/pypi/v/openai_api_call.svg)](https://pypi.python.org/pypi/openai_api_call)
[![Tests](https://github.com/RexWzh/openai_api_call/actions/workflows/test.yml/badge.svg)](https://github.com/RexWzh/openai_api_call/actions/workflows/test.yml/)
[![Documentation Status](https://img.shields.io/badge/docs-github_pages-blue.svg)](https://apicall.wzhecnu.cn)

<!-- 
[![Updates](https://pyup.io/repos/github/RexWzh/openai_api_call/shield.svg)](https://pyup.io/repos/github/RexWzh/openai_api_call/) 
-->

A simple wrapper for OpenAI API, which can send prompt message and return response.

## Installation

```bash
pip install openai-api-call --upgrade
```

> Note: Since version `0.2.0`, `Chat` type is used to handle data, which is not compatible with previous versions.

## Usage

### Set API Key

```py
import openai
openai.api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

Or set `OPENAI_API_KEY` in `~/.bashrc` to automatically set it when you start the terminal:

```bash
# Add the following code to ~/.bashrc
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### Set Proxy (Optional)

```py
from openai_api_call import proxy_on, proxy_off, proxy_status
# Check the current proxy
proxy_status()

# Set local proxy, port number is 7890 by default
proxy_on("127.0.0.1", port=7890)

# Check the updated proxy
proxy_status()

# Turn off proxy
proxy_off() 
```

### Basic Usage

Example 1, send prompt and return information:

```python
from openai_api_call import Chat, show_apikey

# Check if API key is set
show_apikey()

# Check if proxy is enabled
proxy_status()

# Send prompt and return response
chat = Chat("Hello, GPT-3.5!")
resp = chat.getresponse(update=False) # Do not update the chat history, default is True
```

Example 2, customize the message template and return the information and the number of consumed tokens:

```python
import openai_api_call

# Customize the sending template
openai_api_call.default_prompt = lambda msg: [
    {"role": "system", "content": "帮我翻译这段文字"},
    {"role": "user", "content": msg}
]
chat = Chat("Hello!")
# Set the number of retries to Inf
response = chat.getresponse(temperature=0.5, max_requests=-1)
print("Number of consumed tokens: ", response.total_tokens)
print("Returned content: ", response.content)
```

### Advanced Usage

Continue chatting based on the last response:

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

# print chat history
chat.print_log()
```

## License

This package is licensed under the MIT license. See the LICENSE file for more details.

## Features

* update documentation of the repo.