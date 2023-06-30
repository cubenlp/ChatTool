# OpenAI API 
[![PyPI version](https://img.shields.io/pypi/v/openai_api_call.svg)](https://pypi.python.org/pypi/openai_api_call)
[![Tests](https://github.com/cubenlp/openai_api_call/actions/workflows/test.yml/badge.svg)](https://github.com/cubenlp/openai_api_call/actions/workflows/test.yml/)
[![Documentation Status](https://img.shields.io/badge/docs-github_pages-blue.svg)](https://apicall.wzhecnu.cn)

<!-- 
[![Updates](https://pyup.io/repos/github/cubenlp/openai_api_call/shield.svg)](https://pyup.io/repos/github/cubenlp/openai_api_call/) 
-->

OpenAI API 的简单封装，用于发送 prompt 并返回 response。

## 安装方法

```bash
pip install openai-api-call --upgrade
```

## 使用方法

### 设置 API 密钥

```py
import openai_api_call as apicall
apicall.api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

或者直接在 `~/.bashrc` 中设置 `OPENAI_API_KEY`，每次启动终端可以自动设置：

```bash
# 在 ~/.bashrc 中添加如下代码
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

当然，你也可以为每个 `Chat` 对象设置不同的 `api_key`：

```py
from openai_api_call import Chat
chat = Chat("hello")
chat.api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 设置代理（可选）

```py
from openai_api_call import proxy_on, proxy_off, proxy_status
# 查看当前代理
proxy_status()

# 设置代理，这里 IP 127.0.0.1 代表本机
proxy_on(http="127.0.0.1:7890", https="127.0.0.1:7890")

# 查看更新后的代理
proxy_status()

# 关闭代理
proxy_off() 
```

或者，你也可以使用代理 URL 来发送请求，如下所示：

```py
from openai_api_call import request

# 设置代理 URL
request.bash_url = "https://api.example.com"
```

同样地，可以在环境变量指定 `OPENAI_BASE_URL` 来自动设置。

### 基本使用

示例一，发送 prompt 并返回信息：
```python
from openai_api_call import Chat, show_apikey, proxy_status

# 检查 API 密钥是否设置
show_apikey()

# 查看是否开启代理
proxy_status()

# 发送 prompt 并返回 response
chat = Chat("Hello, GPT-3.5!")
resp = chat.getresponse(update=False) # 不更新对话历史，默认为 True
print(resp.content)
```

示例二，自定义消息模板，并返回信息和消耗的 tokens 数量：

```python
import openai_api_call

# 自定义发送模板
openai_api_call.default_prompt = lambda msg: [
    {"role": "system", "content": "帮我翻译这段文字"},
    {"role": "user", "content": msg}
]
chat = Chat("Hello!")

# 设置重试次数为 Inf，超时时间为 10s
response = chat.getresponse(temperature=0.5, max_requests=-1, timeout=10)
print("Number of consumed tokens: ", response.total_tokens)
print("Returned content: ", response.content)

# 重置默认 Prompt
apicall.default_prompt = None
```

示例三，多轮对话：

```python
# 初次对话
chat = Chat("Hello, GPT-3.5!")
resp = chat.getresponse() # 更新对话历史，默认为 True
print(resp.content)

# 继续对话
chat.user("How are you?")
next_resp = chat.getresponse()
print(next_resp.content)

# 假装对话历史
chat.user("What's your name?")
chat.assistant("My name is GPT-3.5.")

# 打印最后一次谈话
print(chat[-1])

# 保存对话内容
chat.save("chat_history.log", mode="w") # 默认为 "a"

# 打印对话历史
chat.print_log()
```

此外，你可以使用 `Chat` 类的 `show_usage_status` 方法来查看 API 的使用情况：

```py
# 查看默认 API 的使用情况
chat = Chat()
chat.show_usage_status()

# 查看指定 API 的使用情况
chat.api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
chat.show_usage_status()
```

### 进阶用法
将对话历史保存到文件中：

```python
checkpoint = "tmp.log"
# chat 1
chat = Chat()
chat.save(checkpoint, mode="w") # 默认为 "a"
# chat 2
chat = Chat("hello!")
chat.save(checkpoint)
# chat 3
chat.assistant("你好, how can I assist you today?")
chat.save(checkpoint)
```

从文件中加载对话历史：

```python
# 加载 Chat 对象（默认）
chats = load_chats(checkpoint)
assert chats == [Chat(log) for log in chat_logs]
# 仅加载对话历史
chat_logs = load_chats(checkpoint, chat_log_only=True)
# 仅加载最后一条消息
chat_msgs = load_chats(checkpoint, last_message_only=True)
assert chat_msgs == ["", "hello!", "你好, how can I assist you today?"]
```

一般来说，你可以定义函数 `msg2chat` 并使用 `process_chats` 来处理数据：

```python
def msg2chat(msg):
    chat = Chat(api_key=api_key)
    chat.system("You are a helpful translator for numbers.")
    chat.user(f"Please translate the digit to Roman numerals: {msg}")
    chat.getresponse()

checkpath = "tmp.log"
# 处理数据的第一部分
msgs = ["1", "2", "3"]
chats = process_chats(msgs, msg2chat, checkpath, clearfile=True)
# 继续处理数据
msgs = msgs + ["4", "5", "6"]
continue_chats = process_chats(msgs, msg2chat, checkpath)
```

## 开源协议

这个项目使用 MIT 协议开源。

## 更新日志

- 版本 `0.2.0` 改用 `Chat` 类型作为中心交互对象
- 版本 `0.3.0` 开始不依赖模块 `openai.py` ，而是直接使用 `requests` 发送请求
    - 支持对每个 `Chat` 使用不同 API 密钥
    - 支持使用代理链接
- 版本 `0.4.0` 开始，工具维护转至 [CubeNLP](https://github.com/cubenlp) 组织账号
- 版本 `0.5.0` 开始，支持使用 `process_chats` 处理数据，借助 `msg2chat` 函数以及 `checkpoint` 文件
- 版本 `0.6.0` 开始，支持 [function call](https://platform.openai.com/docs/guides/gpt/function-calling) 功能