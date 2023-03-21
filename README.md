> 以下为 ChatGPT 自动生成的 README.md 文件（待修改），中文文档移步[这里](README_zh_CN.md)。

# Openai API call
[![PyPI version](https://img.shields.io/pypi/v/openai_api_call.svg)](https://pypi.python.org/pypi/openai_api_call)
[![Tests](https://github.com/RexWzh/openai_api_call/actions/workflows/test.yml/badge.svg)](https://github.com/RexWzh/openai_api_call/actions/workflows/test.yml/)
[![Documentation Status](https://readthedocs.org/projects/openai-api-call/badge/?version=latest)](https://openai-api-call.readthedocs.io/en/latest/?version=latest)

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
from openai_api_call import prompt2response, show_apikey

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

# next call
next_prompt = resp.next_prompt("How are you?")
print(next_prompt)
next_resp = prompt2response(next_prompt)
print(next_resp.content)

# print chat history
list(map(print,next_resp.chat_log()))
```

## License

This package is licensed under the MIT license. See the LICENSE file for more details.

## Features

* TODO

## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage) project template.
