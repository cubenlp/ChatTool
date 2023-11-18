> **中文文档移步[这里](README_zh_CN.md)。**

# ChatAPI Toolkit
[![PyPI version](https://img.shields.io/pypi/v/chattool.svg)](https://pypi.python.org/pypi/chattool)
[![Tests](https://github.com/cubenlp/chattool/actions/workflows/test.yml/badge.svg)](https://github.com/cubenlp/chattool/actions/workflows/test.yml/)
[![Documentation Status](https://img.shields.io/badge/docs-github_pages-blue.svg)](https://chattool.cubenlp.com)
[![Coverage](https://codecov.io/gh/cubenlp/chattool/branch/master/graph/badge.svg)](https://codecov.io/gh/cubenlp/chattool)

<!-- 
[![Updates](https://pyup.io/repos/github/cubenlp/chattool/shield.svg)](https://pyup.io/repos/github/cubenlp/chattool/) 
-->

Toolkit for Chat API, supporting multi-turn dialogue, proxy, and asynchronous data processing.

## Installation

```bash
pip install chattool --upgrade
```

## Usage

### Set API Key and Base URL

Set environment variables in `~/.bashrc` or `~/.zshrc`:

```bash
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export OPENAI_API_BASE_URL="https://api.example.com"
export OPENAI_API_BASE="https://api.example.com/v1"
```

## Examples

Example 1, simulate multi-turn dialogue:

```python
# first chat
chat = Chat("Hello, GPT-3.5!")
resp = chat.getresponse()

# continue the chat
chat.user("How are you?")
next_resp = chat.getresponse()

# add response manually
chat.user("What's your name?")
chat.assistant("My name is GPT-3.5.")

# save the chat history
chat.save("chat.json", mode="w") # default to "a"

# print the chat history
chat.print_log()
```

Example 2, process data in batch, and use a checkpoint file `checkpoint`:

```python
# write a function to process the data
def msg2chat(msg):
    chat = Chat()
    chat.system("You are a helpful translator for numbers.")
    chat.user(f"Please translate the digit to Roman numerals: {msg}")
    chat.getresponse()

checkpoint = "chat.jsonl"
msgs = ["%d" % i for i in range(1, 10)]
# process the data
chats = process_chats(msgs[:5], msg2chat, checkpoint, clearfile=True)
# process the rest data, and read the cache from the last time
continue_chats = process_chats(msgs, msg2chat, checkpoint)
```

Example 3, process data in batch (asynchronous), print hello using different languages, and use two coroutines:

```python
from chattool import async_chat_completion, load_chats

langs = ["python", "java", "Julia", "C++"]
chatlogs = ["print hello using %s" % lang for lang in langs]
async_chat_completion(chatlogs, chkpoint="async_chat.jsonl", ncoroutines=2)
chats = load_chats("async_chat.jsonl")
```

## License

This package is licensed under the MIT license. See the LICENSE file for more details.

## update log

Current version: `2.3.0`. The features of function call, asynchronous processing, and finetuning are supported.

### Beta version
- Since version `0.2.0`, `Chat` type is used to handle data
- Since version `0.3.0`, you can use different API Key to send requests.
- Since version `0.4.0`, this package is mantained by [cubenlp](https://github.com/cubenlp).
- Since version `0.5.0`, one can use `process_chats` to process the data, with a customized `msg2chat` function and a checkpoint file.
- Since version `0.6.0`, the feature [function call](https://platform.openai.com/docs/guides/gpt/function-calling) is added.
- Since version `1.0.0`, the feature [function call](https://platform.openai.com/docs/guides/gpt/function-calling) is removed, and the asynchronous processing tool is added.
- Since version `2.0.0`, the package is renamed to `chattool`, and the asynchronous processing tool is improved.