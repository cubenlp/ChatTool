# OpenAI API 
[![PyPI version](https://img.shields.io/pypi/v/openai_api_call.svg)](https://pypi.python.org/pypi/openai_api_call)
[![Tests](https://github.com/RexWzh/openai_api_call/actions/workflows/test.yml/badge.svg)](https://github.com/RexWzh/openai_api_call/actions/workflows/test.yml/)
[![Documentation Status](https://img.shields.io/badge/docs-github_pages-blue.svg)](https://apicall.wzhecnu.cn)

<!-- 
[![Updates](https://pyup.io/repos/github/RexWzh/openai_api_call/shield.svg)](https://pyup.io/repos/github/RexWzh/openai_api_call/) 
-->

OpenAI API 的简单封装，用于发送 prompt message 并返回 response。

## 安装方法

```bash
pip install openai-api-call --upgrade
```

> 注：版本 `0.2.0` 起改用 `Chat` 类型来处理数据，不兼容之前的版本。

## 使用方法

### 设置 API 密钥

```py
import openai
openai.api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

或者直接在 `~/.bashrc` 中设置 `OPENAI_API_KEY`，每次启动终端可以自动设置：

```bash
# 在 ~/.bashrc 中添加如下代码
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 设置代理（可选）

```py
from openai_api_call import proxy_on, proxy_off, proxy_status
# 查看当前代理
proxy_status()

# 设置本地代理，端口号默认为 7890
proxy_on("127.0.0.1", port=7890)

# 查看更新后的代理
proxy_status()

# 关闭代理
proxy_off() 
```

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
# 设置重试次数为 Inf
response = chat.getresponse(temperature=0.5, max_requests=-1)
print("Number of consumed tokens: ", response.total_tokens)
print("Returned content: ", response.content)
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

# 打印对话历史
chat.print_log()
```

## 开源协议

这个项目使用 MIT 协议开源。

## 未来计划

* 更新仓库文档