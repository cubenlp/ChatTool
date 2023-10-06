# ChatAPI Toolkit
[![PyPI version](https://img.shields.io/pypi/v/chattool.svg)](https://pypi.python.org/pypi/chattool)
[![Tests](https://github.com/cubenlp/chatapi_toolkit/actions/workflows/test.yml/badge.svg)](https://github.com/cubenlp/chatapi_toolkit/actions/workflows/test.yml/)
[![Documentation Status](https://img.shields.io/badge/docs-github_pages-blue.svg)](https://apicall.wzhecnu.cn)
[![Coverage](https://codecov.io/gh/cubenlp/chatapi_toolkit/branch/master/graph/badge.svg)](https://codecov.io/gh/cubenlp/chatapi_toolkit)

<!-- 
[![Updates](https://pyup.io/repos/github/cubenlp/chattool/shield.svg)](https://pyup.io/repos/github/cubenlp/chattool/) 
-->

基于对话 API 的工具包，支持多轮对话，代理，以及异步处理数据等，当前支持 openai 的 API。

## 安装方法

```bash
pip install chattool --upgrade
```

## 使用方法

### 设置密钥和代理链接

设置环境变量，在 `~/.bashrc` 或者 `~/.zshrc` 中追加

```bash
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export OPENAI_BASE_URL="https://api.example.com"
export OPENAI_API_BASE="https://api.example.com/v1"
```

Win 在系统中设置环境变量。

### 示例

示例1，模拟多轮对话：

```python
# 初次对话
chat = Chat("Hello, GPT-3.5!")
resp = chat.getresponse()

# 继续对话
chat.user("How are you?")
next_resp = chat.getresponse()

# 人为添加返回内容
chat.user("What's your name?")
chat.assistant("My name is GPT-3.5.")

# 保存对话内容
chat.save("chat.json", mode="w") # 默认为 "a"

# 打印对话历史
chat.print_log()
```

示例二，批量处理数据（串行），并使用缓存文件 `checkpoint`：

```python
# 编写处理函数
def msg2chat(msg):
    chat = Chat()
    chat.system("You are a helpful translator for numbers.")
    chat.user(f"Please translate the digit to Roman numerals: {msg}")
    chat.getresponse()

checkpoint = "chat.jsonl"
msgs = ["%d" % i for i in range(10)]
# 处理前5个数据，将结果缓存到 checkpoint 文件中
chats = process_chats(msgs[:5], msg2chat, checkpoint, clearfile=True)
# 处理所有数据，并从上一次结果中读取缓存
continue_chats = process_chats(msgs, msg2chat, checkpoint)
```

示例三，批量处理数据（异步并行），用不同语言打印 hello，并使用两个协程：

```python
from chattool import async_chat_completion, load_chats

langs = ["python", "java", "Julia", "C++"]
chatlogs = ["print hello using %s" % lang for lang in langs]
async_chat_completion(chatlogs, chkpoint="async_chat.jsonl", ncoroutines=2)
chats = load_chats("async_chat.jsonl")
```

## 开源协议

这个项目使用 MIT 协议开源。

## 更新日志

当前版本为 `2.3.0`，支持调用外部工具，异步处理数据，以及模型微调功能。

### 测试版本
- 版本 `0.2.0` 改用 `Chat` 类型作为中心交互对象
- 版本 `0.3.0` 开始不依赖模块 `openai.py` ，而是直接使用 `requests` 发送请求
    - 支持对每个 `Chat` 使用不同 API 密钥
    - 支持使用代理链接
- 版本 `0.4.0` 开始，工具维护转至 [CubeNLP](https://github.com/cubenlp) 组织账号
- 版本 `0.5.0` 开始，支持使用 `process_chats` 处理数据，借助 `msg2chat` 函数以及 `checkpoint` 文件
- 版本 `0.6.0` 开始，支持 [function call](https://platform.openai.com/docs/guides/gpt/function-calling) 功能
- 版本 `1.0.0` 开始，支持异步处理数据
- 版本 `2.0.0` 开始，模块更名为 `chattool`