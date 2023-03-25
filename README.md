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
pip install openai-api-call
```

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
from openai_api_call import proxy_on, proxy_off, show_proxy
# Check the current proxy
show_proxy()

# Set local proxy, port number is 7890 by default
proxy_on("127.0.0.1", port=7890)

# Check the updated proxy
show_proxy()

# Turn off proxy
proxy_off() 
```

### Basic Usage

Example 1, send prompt and return information:

```python
from openai_api_call import prompt2response, show_apikey, show_proxy

# Check if API key is set
show_apikey()

# Check if proxy is enabled
show_proxy()

# Send prompt and return response
prompt = "Hello, GPT-3.5!"
resp = prompt2response(prompt)
print(resp.content)
```

Example 2, customize the message template and return the information and the number of consumed tokens:

```python
import openai_api_call
from openai_api_call import prompt2response

# Customize the sending template
openai_api_call.default_prompt = lambda msg: [
    {"role": "system", "content": "帮我翻译这段文字"},
    {"role": "user", "content": msg}
]
prompt = "Hello!"
# Set the number of retries to Inf
response = prompt2response(prompt, temperature=0.5, max_requests=-1)
print("Number of consumed tokens: ", response.total_tokens)
print("Returned content: ", response.content)
```

### Advanced Usage

Continue chatting based on the last response:

```python
# first call
prompt = "Hello, GPT-3.5!"
resp = prompt2response(prompt)
print(resp.content)

# continue chatting
chat = resp.chat
chat.user("How are you?")
next_resp = prompt2response(chat)
print(next_resp.content)

# print chat history
next_resp.chat.print_log()
```

## License

This package is licensed under the MIT license. See the LICENSE file for more details.

## Features-TODO

* update documentation of the repo.
* set access delay.
* set access interval.
* set key pool.
* allow concurrent access.
* create new Chat type variable.