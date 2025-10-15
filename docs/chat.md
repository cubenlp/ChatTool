# Chat 对象使用指南

## 概述

`Chat` 是 Chattool 的核心对话管理接口，它是一个智能工厂函数，能够根据配置类型自动选择合适的客户端实现（OpenAI 或 Azure OpenAI），提供统一、简洁的对话管理功能。

## 核心特性

- **智能客户端选择**：根据配置类型自动选择 OpenAI 或 Azure OpenAI 客户端
- **链式调用**：支持方法链式调用，代码更简洁易读
- **对话历史管理**：自动维护完整的对话上下文
- **同步/异步支持**：提供同步和异步两种调用方式
- **流式响应**：支持实时流式响应
- **错误处理与重试**：内置重试机制和错误处理
- **持久化支持**：支持对话历史的保存和加载
- **调试工具**：提供丰富的调试和监控功能

## 快速开始

### 基本使用

```python
from chattool import Chat

# 使用默认 OpenAI 配置
chat = Chat()

# 基本对话
response = chat.user("你好，请介绍一下自己").get_response()
print(response.content)

# 链式调用
chat.user("什么是机器学习？").assistant("机器学习是...").user("能举个例子吗？")
response = chat.get_response()
print(response.content)
```

### 使用自定义配置

```python
from chattool import Chat
from chattool.core.config import OpenAIConfig, AzureOpenAIConfig

# OpenAI 配置
openai_config = OpenAIConfig(
    api_key="your-openai-api-key",
    model="gpt-4",
    temperature=0.7,
    max_tokens=1000
)
chat = Chat(config=openai_config)

# Azure OpenAI 配置
azure_config = AzureOpenAIConfig(
    api_key="your-azure-api-key",
    api_base="https://your-resource.openai.azure.com/",
    api_version="2023-12-01-preview",
    model="gpt-4",
    temperature=0.7
)
chat = Chat(config=azure_config)
```

## API 参考

### Chat 工厂函数

```python
def Chat(
    config: Optional[Union[OpenAIConfig, AzureOpenAIConfig]] = None,
    logger: Optional[logging.Logger] = None,
    **kwargs
) -> Union[ChatOpenAI, ChatAzure]
```

**参数：**
- `config`: 配置对象（OpenAIConfig 或 AzureOpenAIConfig）
- `logger`: 自定义日志实例
- `**kwargs`: 其他配置参数

**返回：**
- 根据配置类型返回 ChatOpenAI 或 ChatAzure 实例

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
response = chat.user("什么是人工智能？").get_response()
print(response.content)

# 带参数的响应
response = chat.get_response(
    temperature=0.8,
    max_tokens=500,
    top_p=0.9
)

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
    response = await chat.user("解释一下区块链技术").get_response_async()
    print(response.content)
    
    # 异步快速问答
    answer = await chat.ask_async("什么是NFT？")
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
    async for chunk in chat.user("写一首关于春天的诗").get_response_stream_async():
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

### Azure OpenAI 配置

```python
from chattool.core.config import AzureOpenAIConfig

# Azure 配置
azure_config = AzureOpenAIConfig(
    api_key="your-azure-key",
    api_base="https://your-resource.openai.azure.com/",
    api_version="2023-12-01-preview",
    model="gpt-4"
)

chat = Chat(config=azure_config)
```

## 高级用法

### 批量处理

```python
import asyncio

async def batch_questions():
    chat = Chat()
    
    questions = [
        "什么是机器学习？",
        "什么是深度学习？", 
        "什么是神经网络？"
    ]
    
    tasks = []
    for question in questions:
        # 为每个问题创建独立的对话副本
        chat_copy = chat.copy()
        task = chat_copy.user(question).get_response_async()
        tasks.append(task)
    
    # 并发执行
    responses = await asyncio.gather(*tasks)
    
    for i, response in enumerate(responses):
        print(f"问题 {i+1}: {questions[i]}")
        print(f"回答: {response.content}\n")

# 运行批量处理
asyncio.run(batch_questions())
```

### 对话模板

```python
def create_translator_chat():
    """创建翻译助手"""
    chat = Chat()
    chat.system("你是一个专业的翻译助手，能够准确翻译中英文。")
    return chat

def create_code_reviewer_chat():
    """创建代码审查助手"""
    chat = Chat()
    chat.system("你是一个资深的代码审查专家，能够发现代码中的问题并提供改进建议。")
    return chat

# 使用模板
translator = create_translator_chat()
answer = translator.ask("请将'Hello World'翻译成中文")
print(answer)
```

## 最佳实践

### 1. 配置管理

```python
# 推荐：使用配置类
config = OpenAIConfig(
    model="gpt-4",
    temperature=0.7,
    max_tokens=1000
)
chat = Chat(config=config)

# 避免：在每次调用时传递参数
# chat.get_response(model="gpt-4", temperature=0.7)  # 不推荐
```

### 2. 错误处理

```python
def safe_chat(question: str, max_retries: int = 3) -> str:
    """安全的对话函数"""
    chat = Chat()
    
    for attempt in range(max_retries):
        try:
            return chat.user(question).ask()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            print(f"尝试 {attempt + 1} 失败: {e}")
    
    return "无法获取响应"
```

### 3. 对话管理

```python
# 推荐：定期保存重要对话
chat = Chat()
# ... 进行对话 ...
chat.save(f"important_conversation_{int(time.time())}.jsonl")

# 推荐：使用副本进行实验
original_chat = Chat()
# ... 建立基础对话 ...

# 创建副本进行不同的尝试
experiment1 = original_chat.copy()
experiment2 = original_chat.copy()
```

### 4. 性能优化

```python
# 异步处理多个请求
async def efficient_batch_processing():
    chat = Chat()
    
    # 使用异步方法
    tasks = [
        chat.copy().user(q).get_response_async() 
        for q in questions
    ]
    
    responses = await asyncio.gather(*tasks)
    return responses
```

## 完整示例

```python
import asyncio
from chattool import Chat
from chattool.core.config import OpenAIConfig

async def complete_example():
    """完整的使用示例"""
    
    # 1. 创建配置
    config = OpenAIConfig(
        model="gpt-4",
        temperature=0.7,
        max_tokens=1000
    )
    
    # 2. 创建对话
    chat = Chat(config=config)
    
    # 3. 设置系统消息
    chat.system("你是一个有用的AI助手，能够回答各种问题。")
    
    # 4. 进行对话
    print("=== 同步对话 ===")
    response = chat.user("什么是人工智能？").get_response()
    print(f"AI: {response.content}")
    
    # 5. 异步对话
    print("\n=== 异步对话 ===")
    response = await chat.user("AI的发展历史如何？").get_response_async()
    print(f"AI: {response.content}")
    
    # 6. 流式响应
    print("\n=== 流式响应 ===")
    print("AI: ", end='')
    async for chunk in chat.user("请写一首关于技术的诗").get_response_stream_async():
        print(chunk.content, end='', flush=True)
    print()
    
    # 7. 保存对话
    chat.save("example_conversation.jsonl")
    
    # 8. 显示调试信息
    print("\n=== 调试信息 ===")
    chat.print_debug_info()

# 运行完整示例
if __name__ == "__main__":
    asyncio.run(complete_example())
```

这个文档基于实际的示例代码，提供了 Chat 对象的全面使用指南，涵盖了从基础用法到高级特性的所有内容。