> **中文文档移步[这里](README_zh_CN.md)。**

# ChatAPI Toolkit
[![PyPI version](https://img.shields.io/pypi/v/chattool.svg)](https://pypi.python.org/pypi/chattool)
[![Tests](https://github.com/cubenlp/chatapi_toolkit/actions/workflows/test.yml/badge.svg)](https://github.com/cubenlp/chatapi_toolkit/actions/workflows/test.yml/)
[![Documentation Status](https://img.shields.io/badge/docs-github_pages-blue.svg)](https://chattool.cubenlp.com)
[![Coverage](https://codecov.io/gh/cubenlp/chatapi_toolkit/branch/master/graph/badge.svg)](https://codecov.io/gh/cubenlp/chatapi_toolkit)

<!-- 
[![Updates](https://pyup.io/repos/github/cubenlp/chattool/shield.svg)](https://pyup.io/repos/github/cubenlp/chattool/) 
-->

Toolkit for Chat API, supporting multi-turn dialogue, proxy, and asynchronous data processing.

## Installation

```bash
pip install chattool --upgrade
```

## Usage

Set environment variables in `~/.bashrc` or `~/.zshrc`:

```bash
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export OPENAI_API_BASE_URL="https://api.example.com"
export OPENAI_API_BASE="https://api.example.com/v1"
```

Simulate multi-turn dialogue:

```python
# first chat
chat = Chat("Hello, GPT-3.5!")
resp = chat.getresponse()

# add response manually
chat.user("What's your name?")
chat.assistant("My name is GPT-3.5.")

# save the chat history
chat.save("chat.json", mode="w") # default to "a"

# print the chat history
chat.print_log()
```

For more cases, please refer to [ChatTool Documentation](https://chattool.cubenlp.com).

## License

This package is licensed under the MIT license. See the LICENSE file for more details.

### Update log

- Since version `2.3.0`, the feature of finetuning is added.
- Since version `2.0.0`, the package is renamed to `chattool`, and the asynchronous processing tool is improved.
- Since version `1.0.0`, the feature [function call](https://platform.openai.com/docs/guides/gpt/function-calling) is removed, and the asynchronous processing tool is added.
- Since version `0.6.0`, the feature [function call](https://platform.openai.com/docs/guides/gpt/function-calling) is added.
- Since version `0.5.0`, one can use `process_chats` to process the data, with a customized `msg2chat` function and a checkpoint file.
- Since version `0.4.0`, this package is mantained by [cubenlp](https://github.com/cubenlp).
- Since version `0.3.0`, you can use different API Key to send requests.
- Since version `0.2.0`, `Chat` type is used to handle data
- Since version `0.1.0`, multi-turn dialogue is supported