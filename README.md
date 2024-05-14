<div align="center">
    <a href="https://pypi.python.org/pypi/chattool">
        <img src="https://img.shields.io/pypi/v/chattool.svg" alt="PyPI version" />
    </a>
    <a href="https://github.com/cubenlp/chattool/actions/workflows/test.yml">
        <img src="https://github.com/cubenlp/chattool/actions/workflows/test.yml/badge.svg" alt="Tests" />
    </a>
    <a href="https://chattool.cubenlp.com">
        <img src="https://img.shields.io/badge/docs-github_pages-blue.svg" alt="Documentation Status" />
    </a>
    <a href="https://codecov.io/gh/cubenlp/chattool">
        <img src="https://codecov.io/gh/cubenlp/chattool/branch/master/graph/badge.svg" alt="Coverage" />
    </a>
</div>

<div align="center">
    <img src="https://qiniu.wzhecnu.cn/PicBed6/picgo/chattool.jpeg" alt="ChatAPI Toolkit" width="360", style="border-radius: 20px;">

[English](README_en.md) | [简体中文](README.md)
</div>

基于 OpenAI API 的 `Chat` 对象，支持多轮对话，代理，以及异步处理数据等。

## 安装方法

```bash
pip install chattool --upgrade
```

## 使用方法

### 设置密钥和代理链接

通过环境变量设置密钥和代理，比如在 `~/.bashrc` 或者 `~/.zshrc` 中追加

```bash
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export OPENAI_API_BASE="https://api.example.com/v1"
export OPENAI_API_BASE_URL="https://api.example.com" # 可选
```

或者在代码中设置：

```py
import chattool
chattool.api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
chattool.api_base = "https://api.example.com/v1"
```

注：环境变量 `OPENAI_API_BASE` 优先于 `OPENAI_API_BASE_URL`，二者选其一即可。

### 示例

示例1，多轮对话：

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

示例2，批量处理数据（串行），并使用缓存文件 `chat.jsonl`：

```python
# 编写处理函数
def data2chat(msg):
    chat = Chat()
    chat.system("你是一个熟练的数字翻译家。")
    chat.user(f"请将该数字翻译为罗马数字：{msg}")
    # 注意，在函数内获取返回
    chat.getresponse()
    return chat

checkpoint = "chat.jsonl" # 缓存文件的名称
msgs = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
# 处理数据，如果 checkpoint 存在，则从上次中断处继续
continue_chats = process_chats(msgs, data2chat, checkpoint)
```

示例3，批量处理数据（异步并行），用不同语言打印 hello，并使用两个协程：

```python
from chattool import async_chat_completion, load_chats, Chat

langs = ["python", "java", "Julia", "C++"]
def data2chat(msg):
    chat = Chat()
    chat.user("请用语言 %s 打印 hello world" % msg)
    # 注意，这里不需要 getresponse 而交给异步处理
    return chat

async_chat_completion(langs, chkpoint="async_chat.jsonl", nproc=2, data2chat=data2chat)
chats = load_chats("async_chat.jsonl")
```

在 Jupyter Notebook 中运行，因其[特殊机制](https://stackoverflow.com/questions/47518874/how-do-i-run-python-asyncio-code-in-a-jupyter-notebook)，需使用 `await` 关键字和 `wait=True` 参数：

```python
await async_chat_completion(langs, chkpoint="async_chat.jsonl", nproc=2, data2chat=data2chat, wait=True)
```

示例4，使用工具（自定义函数）：

```python
# 定义函数
def add(a: int, b: int) -> int:
    """
    This function adds two numbers.

    Parameters:
        a (int): The first number.
        b (int): The second number.

    Returns:
        int: The sum of the two numbers.
    """
    return a + b
# 传输函数
chat = Chat()
chat.setfuncs([add]) # 传入函数列表，可以是多个函数
chat.user("请计算 1 + 2")
# 自动调用工具
chat.autoresponse(display=True)
```

## 开源协议

这个项目使用 MIT 协议开源。

## 更新日志

- 版本 `2.3.0`，支持调用外部工具，异步处理数据，以及模型微调功能
- 版本 `2.0.0` 开始，更名为 `chattool`
- 版本 `1.0.0` 开始，支持异步处理数据
- 版本 `0.6.0` 开始，支持 [function call](https://platform.openai.com/docs/guides/gpt/function-calling) 功能
- 版本 `0.5.0` 开始，支持使用 `process_chats` 处理数据，借助 `msg2chat` 函数以及 `checkpoint` 文件
- 版本 `0.4.0` 开始，工具维护转至 [CubeNLP](https://github.com/cubenlp) 组织账号
- 版本 `0.3.0` 开始不依赖模块 `openai.py` ，而是直接使用 `requests` 发送请求
    - 支持对每个 `Chat` 使用不同 API 密钥
    - 支持使用代理链接
- 版本 `0.2.0` 改用 `Chat` 类型作为中心交互对象