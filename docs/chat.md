# Chat 对象文档

## 概述

<mcfile name="chattype.py" path="/Users/wangzhihong/workspace/python/chattool/src/chattool/core/chattype.py"></mcfile> 中的 <mcsymbol name="Chat" filename="chattype.py" path="/Users/wangzhihong/workspace/python/chattool/src/chattool/core/chattype.py" startline="13" type="function"></mcsymbol> 是 ChatTool 的核心对话管理接口。它是一个工厂函数，根据配置类型自动选择合适的客户端实现（OpenAI 或 Azure OpenAI），提供统一的对话管理功能。

## 核心特性

- **智能客户端选择**：根据配置类型自动选择 OpenAI 或 Azure OpenAI 客户端
- **对话历史管理**：自动维护完整的对话上下文
- **同步/异步支持**：提供同步和异步两种调用方式
- **错误处理与重试**：内置重试机制和错误处理
- **持久化支持**：支持对话历史的保存和加载
- **链式调用**：支持方法链式调用，提高代码可读性

## 快速开始

### 基本使用

```python
from chattool import Chat

# 使用默认 OpenAI 配置
chat = Chat()

# 添加消息并获取响应
response = chat.user("你好，请介绍一下自己").get_response()
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
    temperature=0.7
)
chat = Chat(config=openai_config)

# Azure OpenAI 配置
azure_config = AzureOpenAIConfig(
    api_key="your-azure-api-key",
    api_base="https://your-resource.openai.azure.com/",
    api_version="2023-12-01-preview",
    model="gpt-4"
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
) -> 'ChatBase'
```

**参数：**
- `config`: 配置对象，支持 `OpenAIConfig` 或 `AzureOpenAIConfig`
- `logger`: 自定义日志记录器
- `**kwargs`: 其他配置参数

**返回：**
- 返回 `ChatOpenAI` 或 `ChatAzure` 实例

## 消息管理

### 添加消息

```python
# 方法1：使用便捷方法
chat.user("用户消息")
chat.assistant("助手回复")
chat.system("系统提示")

# 方法2：使用通用方法
chat.add_message("user", "用户消息")
chat.add_message("assistant", "助手回复")
chat.add_message("system", "系统提示")

# 链式调用
chat.system("你是一个有用的助手").user("请介绍一下Python")
```

### 消息历史操作

```python
# 查看对话历史
print(chat.chat_log)

# 获取最后一条消息
print(chat.last_message)

# 获取消息数量
print(len(chat))

# 访问特定消息
print(chat[0])  # 第一条消息
print(chat[-1])  # 最后一条消息

# 删除最后一条消息
removed_message = chat.pop()

# 清空对话历史
chat.clear()
```

## 获取响应

### 同步响应

```python
# 基本用法
response = chat.get_response()
print(response.content)

# 带参数
response = chat.get_response(
    temperature=0.8,
    max_tokens=150,
    max_retries=5,
    retry_delay=2.0
)

# 便捷问答方法
answer = chat.ask("什么是人工智能？")
print(answer)
```

### 异步响应

```python
import asyncio

async def main():
    # 异步获取响应
    response = await chat.async_get_response()
    print(response.content)
    
    # 异步问答
    answer = await chat.async_ask("什么是机器学习？")
    print(answer)

asyncio.run(main())
```

### 响应参数

- `max_retries`: 最大重试次数（默认：3）
- `retry_delay`: 重试延迟时间（默认：1.0秒）
- `update_history`: 是否更新对话历史（默认：True）
- `temperature`: 温度参数
- `max_tokens`: 最大token数
- `top_p`: top_p 参数
- 其他 OpenAI API 支持的参数

## 响应对象

### ChatResponse 属性

```python
response = chat.get_response()

# 基本信息
print(response.id)          # 响应ID
print(response.model)       # 使用的模型
print(response.created)     # 创建时间戳

# 消息内容
print(response.content)     # 响应内容
print(response.role)        # 消息角色
print(response.message)     # 完整消息对象

# Token 使用统计
print(response.total_tokens)      # 总token数
print(response.prompt_tokens)     # 提示token数
print(response.completion_tokens) # 完成token数
print(response.usage)             # 完整使用统计

# 完成信息
print(response.finish_reason)     # 完成原因

# 错误处理
if not response.is_valid():
    print(response.error_message)
```

## 对话持久化

### 保存对话

```python
# 保存到文件
chat.save("conversation.jsonl")

# 追加模式保存
chat.save("conversation.jsonl", mode='a', index=1)
```

### 加载对话

```python
# 从文件加载
chat = Chat.load("conversation.jsonl")

# 继续对话
response = chat.user("继续我们之前的对话").get_response()
```

## 对话复制

```python
# 复制当前对话状态
new_chat = chat.copy()

# 在新对话中尝试不同的问题
new_chat.user("换个角度思考这个问题").get_response()
```

## 调试和监控

### 调试信息

```python
# 打印对话历史
chat.print_log()

# 获取调试信息
debug_info = chat.get_debug_info()
print(debug_info)

# 打印调试信息
chat.print_debug_info()

# 获取最后一次响应
last_response = chat.last_response
if last_response:
    last_response.print_debug_info()
```

### 日志记录

```python
import logging

# 自定义日志记录器
logger = logging.getLogger("my_chat")
logger.setLevel(logging.DEBUG)

chat = Chat(logger=logger)
```

## 配置管理

### OpenAI 配置

```python
from chattool.core.config import OpenAIConfig

config = OpenAIConfig(
    api_key="your-api-key",
    api_base="https://api.openai.com/v1",  # 可选，默认值
    model="gpt-4",
    temperature=0.7,
    max_tokens=1000,
    top_p=1.0,
    frequency_penalty=0.0,
    presence_penalty=0.0,
    timeout=30.0,
    max_retries=3,
    retry_delay=1.0
)

chat = Chat(config=config)
```

### Azure OpenAI 配置

```python
from chattool.core.config import AzureOpenAIConfig

config = AzureOpenAIConfig(
    api_key="your-azure-api-key",
    api_base="https://your-resource.openai.azure.com/",
    api_version="2023-12-01-preview",
    model="gpt-4",
    temperature=0.7,
    max_tokens=1000,
    timeout=30.0
)

chat = Chat(config=config)
```

### 环境变量配置

Chat 对象支持从环境变量自动读取配置：

**OpenAI 环境变量：**
```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_API_BASE="https://api.openai.com/v1"
export OPENAI_API_MODEL="gpt-4"
```

**Azure OpenAI 环境变量：**
```bash
export AZURE_OPENAI_API_KEY="your-azure-api-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_VERSION="2023-12-01-preview"
export AZURE_OPENAI_API_MODEL="gpt-4"
```

## 错误处理

### 常见错误处理

```python
try:
    response = chat.user("测试消息").get_response()
    print(response.content)
except Exception as e:
    print(f"请求失败: {e}")
    
    # 检查是否是API错误
    if hasattr(e, 'response'):
        print(f"状态码: {e.response.status_code}")
        print(f"错误详情: {e.response.text}")
```

### 重试机制

```python
# 自定义重试参数
response = chat.get_response(
    max_retries=5,      # 最多重试5次
    retry_delay=2.0     # 每次重试间隔2秒
)
```

## 高级用法

### 函数调用

```python
# 定义函数
functions = [
    {
        "name": "get_weather",
        "description": "获取天气信息",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"}
            },
            "required": ["city"]
        }
    }
]

# 使用函数调用
response = chat.user("北京今天天气怎么样？").get_response(
    functions=functions,
    function_call="auto"
)

# 检查是否调用了函数
if response.message.get('function_call'):
    function_name = response.message['function_call']['name']
    function_args = response.message['function_call']['arguments']
    print(f"调用函数: {function_name}")
    print(f"参数: {function_args}")
```

### 流式响应

```python
# 注意：当前版本流式响应功能正在开发中
response = chat.get_response(stream=True)
```

### 批量处理

```python
questions = [
    "什么是人工智能？",
    "机器学习的主要类型有哪些？",
    "深度学习和机器学习的区别是什么？"
]

answers = []
for question in questions:
    # 为每个问题创建独立的对话
    temp_chat = chat.copy().clear()
    answer = temp_chat.ask(question)
    answers.append(answer)
```

## 最佳实践

### 1. 配置管理

```python
# 推荐：使用环境变量
import os
os.environ['OPENAI_API_KEY'] = 'your-api-key'
chat = Chat()  # 自动读取环境变量

# 或者使用配置对象
config = OpenAIConfig(api_key="your-api-key")
chat = Chat(config=config)
```

### 2. 错误处理

```python
def safe_chat(chat, message, max_retries=3):
    """安全的对话函数"""
    try:
        return chat.user(message).get_response(max_retries=max_retries)
    except Exception as e:
        print(f"对话失败: {e}")
        return None
```

### 3. 对话管理

```python
# 定期保存对话历史
chat.save(f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl")

# 控制对话长度
if len(chat) > 20:  # 超过20条消息时
    # 保留系统消息和最近10条消息
    system_messages = [msg for msg in chat.chat_log if msg['role'] == 'system']
    recent_messages = chat.chat_log[-10:]
    chat.clear()
    for msg in system_messages + recent_messages:
        chat.add_message(msg['role'], msg['content'])
```

### 4. 性能优化

```python
# 使用异步处理多个请求
async def process_multiple_questions(questions):
    chat = Chat()
    tasks = []
    
    for question in questions:
        temp_chat = chat.copy().clear()
        task = temp_chat.async_ask(question)
        tasks.append(task)
    
    return await asyncio.gather(*tasks)
```

## 示例代码

### 完整对话示例

```python
from chattool import Chat
from chattool.core.config import OpenAIConfig

# 创建配置
config = OpenAIConfig(
    model="gpt-4",
    temperature=0.7,
    max_tokens=500
)

# 创建对话
chat = Chat(config=config)

# 设置系统提示
chat.system("你是一个专业的Python编程助手，请提供准确和有用的编程建议。")

# 进行对话
try:
    # 第一轮对话
    response1 = chat.user("请解释Python中的装饰器").get_response()
    print("助手:", response1.content)
    
    # 第二轮对话
    response2 = chat.user("能给个具体的装饰器例子吗？").get_response()
    print("助手:", response2.content)
    
    # 保存对话
    chat.save("python_tutorial.jsonl")
    
    # 打印使用统计
    print(f"总token使用: {response2.total_tokens}")
    
except Exception as e:
    print(f"对话出错: {e}")
```

### 异步批量处理示例

```python
import asyncio
from chattool import Chat

async def analyze_texts(texts):
    """异步分析多个文本"""
    chat = Chat()
    chat.system("你是一个文本分析专家，请分析给定文本的情感倾向。")
    
    async def analyze_single(text):
        temp_chat = chat.copy()
        return await temp_chat.async_ask(f"请分析这段文本的情感: {text}")
    
    # 并发处理
    tasks = [analyze_single(text) for text in texts]
    results = await asyncio.gather(*tasks)
    
    return results

# 使用示例
texts = [
    "今天天气真好，心情很愉快！",
    "这个产品质量太差了，很失望。",
    "会议进行得很顺利，大家都很配合。"
]

results = asyncio.run(analyze_texts(texts))
for i, result in enumerate(results):
    print(f"文本{i+1}分析结果: {result}")
```

## 注意事项

1. **API 密钥安全**：不要在代码中硬编码 API 密钥，使用环境变量或配置文件
2. **Token 限制**：注意模型的 token 限制，及时清理过长的对话历史
3. **错误处理**：始终包含适当的错误处理逻辑
4. **异步使用**：在高并发场景下优先使用异步方法
5. **资源管理**：长时间运行的应用中注意内存使用，定期清理不需要的对话历史

## 相关文档

- [配置文档](config.md)
- [客户端文档](client.md)
- [响应对象文档](response.md)
- [API 参考](api.md)