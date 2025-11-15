# Chat 对象使用指南

## 概述

`Chat` 是 Chattool 的核心对话管理类，提供统一、简洁的对话管理功能。它默认从环境变量读取 `OPENAI_API_KEY`、`OPENAI_API_BASE`、`OPENAI_API_MODEL`，也支持在初始化时显式传入参数。

## 快速开始

### 基本使用

```python
from chattool import Chat

# 使用默认 OpenAI 配置
chat = Chat()

# 基本对话
response = chat.ask("你好，请介绍一下自己", update_history=False)
print(response.content)

# 链式调用
chat.user("什么是机器学习？").assistant("机器学习是...").user("能举个例子吗？")
response = chat.get_response()
print(response.content)
```

### 使用显式参数

```python
from chattool import Chat

# 显式传参（未传入则使用环境变量默认值）
chat = Chat(
    api_key="your-openai-api-key",
    api_base="https://api.openai.com/v1",
    model="gpt-4o-mini",
    timeout=30,
    max_retries=3,
    retry_delay=1.0,
)
```

## API 参考

### Chat 初始化参数

```python
Chat(
    messages: Optional[Union[str, List[Dict[str, str]]]] = None,
    logger: Optional[logging.Logger] = None,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    model: Optional[str] = None,
    timeout: float = 0,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    headers: Optional[Dict[str, str]] = None,
    **kwargs,
)
```

未显式传入时将从环境变量读取默认值：`OPENAI_API_KEY`、`OPENAI_API_BASE`、`OPENAI_API_MODEL`。

## 消息管理

### 添加消息

```python
# 方法一：使用便捷方法
chat.user("用户消息")
chat.assistant("助手回复")
chat.system("系统指令")

# 方法二：使用通用方法
chat.add_message("user", "用户消息")
chat.add_message("assistant", "助手回复")
chat.add_message("system", "系统指令")

# 链式调用
chat.system("你是一个有用的助手").user("请帮我解释量子计算")
```

### 历史管理

```python
# 查看对话历史
print(chat.chat_log)

# 获取最后一条消息
print(chat.last_message)

# 移除最后一条消息
removed_message = chat.pop()

# 移除指定位置的消息
removed_message = chat.pop(0)  # 移除第一条消息

# 清空对话历史
chat.clear()

# 获取对话长度
print(len(chat))

# 访问特定消息
first_message = chat[0]
last_message = chat[-1]
```

## 获取响应

### 同步响应

```python
# 基本响应
response = chat.user("什么是人工智能？").get_response(
    temperature=0.8,
    max_tokens=500,
    top_p=0.9
)
print(response.content)

# 快速问答
answer = chat.ask("什么是深度学习？")
print(answer)  # 直接返回字符串内容
```

### 异步响应

```python
import asyncio

async def async_chat_example():
    chat = Chat()
    
    # 异步响应
    response = await chat.user("解释一下区块链技术").async_get_response()
    print(response.content)
    
    # 异步快速问答
    answer = await chat.async_ask("什么是NFT？")
    print(answer)

# 运行异步示例
asyncio.run(async_chat_example())
```

### 流式响应

```python
import asyncio

async def streaming_example():
    chat = Chat()
    
    # 异步流式响应
    async for chunk in chat.user("写一首关于春天的诗").async_get_response_stream():
        print(chunk.content, end='', flush=True)
    print()  # 换行

# 运行流式示例
asyncio.run(streaming_example())
```

## 响应参数

### 常用参数

```python
response = chat.get_response(
    temperature=0.7,        # 创造性控制 (0-2)
    max_tokens=1000,        # 最大令牌数
    top_p=0.9,             # 核采样
    frequency_penalty=0.0,  # 频率惩罚
    presence_penalty=0.0,   # 存在惩罚
    stop=["END", "STOP"]   # 停止词
)
```

### ChatResponse 对象

```python
response = chat.get_response()

# 响应内容
print(response.content)

# 响应元数据
print(response.model)           # 使用的模型
print(response.usage)           # 令牌使用情况
print(response.finish_reason)   # 完成原因
print(response.response_time)   # 响应时间

# 原始响应数据
print(response.raw_response)
```

## 对话管理

### 保存和加载对话

```python
# 保存对话到文件
chat.save("conversation.jsonl")

# 从文件加载对话
chat = Chat.load("conversation.jsonl")

# 保存时指定模式和索引
chat.save("conversations.jsonl", mode='a', index=1)
```

### 复制对话状态

```python
# 创建对话副本
chat_copy = chat.copy()

# 原对话和副本独立操作
chat.user("原始对话")
chat_copy.user("副本对话")
```

## 调试和监控

### 日志和调试信息

```python
# 打印对话历史
chat.print_log()

# 获取调试信息
debug_info = chat.get_debug_info()
print(debug_info)

# 打印调试信息
chat.print_debug_info()

# 访问最后一次响应
if chat.last_response:
    print(f"模型: {chat.last_response.model}")
    print(f"用时: {chat.last_response.response_time}秒")
    print(f"令牌使用: {chat.last_response.usage}")
```

### 错误处理

```python
try:
    response = chat.user("测试消息").get_response()
    print(response.content)
except Exception as e:
    print(f"请求失败: {e}")
    
    # 查看调试信息
    chat.print_debug_info()
```

## 配置管理

### 环境变量配置

```python
# 设置环境变量
import os
os.environ["OPENAI_API_KEY"] = "your-api-key"
os.environ["OPENAI_API_BASE"] = "https://api.openai.com/v1"

# 使用环境变量（自动读取）
chat = Chat()
```

## 完整示例

```python
import asyncio
from chattool import Chat
async def complete_example():
    """完整的使用示例"""
    
    # 1. 创建对话（从环境变量读取默认配置）
    chat = Chat(model="gpt-4o-mini")
    
    # 2. 设置系统消息
    chat.system("你是一个有用的AI助手，能够回答各种问题。")
    
    # 3. 进行对话
    print("=== 同步对话 ===")
    response = chat.user("什么是人工智能？").get_response()
    print(f"AI: {response.content}")
    
    # 4. 异步对话
    print("\n=== 异步对话 ===")
    response = await chat.user("AI的发展历史如何？").async_get_response()
    print(f"AI: {response.content}")
    
    # 5. 流式响应
    print("\n=== 流式响应 ===")
    print("AI: ", end='')
    async for chunk in chat.user("请写一首关于技术的诗").async_get_response_stream():
        print(chunk.content, end='', flush=True)
    print()
    
    # 6. 保存对话
    chat.save("example_conversation.jsonl")
    
    # 7. 显示调试信息
    print("\n=== 调试信息 ===")
    chat.print_debug_info()

# 运行完整示例
if __name__ == "__main__":
    asyncio.run(complete_example())
```
