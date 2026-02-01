# Chattool 客户端使用指南

## 概述

Chattool 提供了两个核心客户端用于与 API 服务交互：

- **HTTPClient**: 通用 HTTP 客户端，提供基础的 HTTP 请求功能
- **Chat**: 基于 OpenAI Chat Completion 的对话客户端，支持同步/异步及流式响应

这些客户端都支持同步和异步操作，具有重试机制、错误处理和连接管理功能。

## HTTPClient

### 概述

HTTPClient 是基础的 HTTP 客户端类，提供了通用的 HTTP 请求功能。它支持 GET、POST、PUT、DELETE 等常见的 HTTP 方法，并提供了同步和异步两种调用方式。

### 基本使用

```python
from chattool.core.request import HTTPClient

# 创建客户端实例
client = HTTPClient()

# 发送 GET 请求
response = client.request(
    method="GET",
    url="http://localhost:8000/get",
    params={"key": "value", "test": "example"}
)
print(f"状态码: {response.status_code}")
print(f"响应内容: {response.json()}")

# 发送 POST 请求
response = client.request(
    method="POST",
    url="http://localhost:8000/post",
    data={"message": "Hello from HTTPClient", "type": "test"}
)
print(f"响应内容: {response.json()}")
```

### 初始化配置

```python
from chattool.core import HTTPClient, HTTPConfig

# 使用默认配置
client = HTTPClient()

# 使用自定义配置
config = HTTPConfig(
    api_base="https://api.example.com",
    timeout=30,
    max_retries=3,
    retry_delay=1.0,
    headers={"User-Agent": "MyApp/1.0"}
)
client = HTTPClient(config)

# 使用 kwargs 直接设置参数
client = HTTPClient(
    api_base="https://api.example.com",
    timeout=30,
    headers={"Authorization": "Bearer token"}
)
```

### 便捷方法

```python
# GET 请求
response = client.get("/api/data", params={"page": 1})

# POST 请求
response = client.post("/api/data", data={"key": "value"})

# PUT 请求
response = client.put("/api/data", data={"key": "updated_value"})

# DELETE 请求
response = client.delete("/api/data")
```

### 自定义请求头

```python
# 方法一：在初始化时设置全局请求头
client = HTTPClient(headers={
    "Authorization": "Bearer your-token",
    "Content-Type": "application/json",
    "User-Agent": "MyApp/1.0"
})

# 方法二：在单次请求中设置请求头
response = client.request(
    method="GET",
    url="http://localhost:8000/headers",
    headers={
        "Authorization": "Bearer token123",
        "X-Custom-Header": "custom-value"
    }
)
```

### 异步操作

```python
import asyncio

async def async_http_example():
    client = HTTPClient()
    
    # 异步 GET 请求
    response = await client.async_request(
        method="GET",
        url="http://localhost:8000/get",
        params={"async": "true"}
    )
    print(f"异步响应: {response.json()}")
    
    # 异步便捷方法
    response = await client.async_get("/api/data")
    response = await client.async_post("/api/data", data={"key": "value"})

# 运行异步示例
asyncio.run(async_http_example())
```

### 上下文管理器

```python
# 同步上下文管理器
with HTTPClient() as client:
    response = client.get("http://localhost:8000/get")
    print(response.json())
# 客户端会自动关闭

# 异步上下文管理器
async def async_context_example():
    async with HTTPClient() as client:
        response = await client.async_get("http://localhost:8000/get")
        print(response.json())
    # 客户端会自动关闭

asyncio.run(async_context_example())
```

### 错误处理

```python
import httpx

def error_handling_example():
    client = HTTPClient()
    
    # 处理 HTTP 错误
    try:
        response = client.request(
            method="GET",
            url="http://127.0.0.1:8000/status/404"
        )
    except httpx.HTTPStatusError as e:
        print(f"HTTP 错误状态码: {e.response.status_code}")
    except Exception as e:
        print(f"HTTP 错误: {e}")
    
    # 处理超时
    try:
        response = client.request(
            method="GET",
            url="http://127.0.0.1:8000/delay/10",
            timeout=2  # 2秒超时
        )
    except Exception as e:
        print(f"超时错误: {type(e).__name__}: {e}")
```

## Chat（对话客户端）

### 概述

`Chat` 基于 OpenAI Chat Completion，提供同步/异步响应与流式输出，并内置对话历史管理与调试工具。

### 基本使用

```python
from chattool import Chat

chat = Chat()
chat.system("你是一个有用的助手")
resp = chat.user("什么是人工智能？").get_response()
print(resp.content)
```

### 异步与流式

```python
import asyncio
from chattool import Chat

async def async_examples():
    chat = Chat()

    # 异步响应
    resp = await chat.user("解释一下量子计算").async_get_response()
    print(resp.content)

    # 流式响应（异步）
    print("流式: ", end='')
    async for chunk in chat.user("写一首关于春天的诗").async_get_response_stream():
        if chunk.delta_content:
            print(chunk.delta_content, end='', flush=True)
    print()

asyncio.run(async_examples())
```

## 配置类

详细配置说明请参考 [配置管理指南](configuration.md)。

### HTTPConfig（基础配置）

```python
from chattool.core.config import HTTPConfig

config = HTTPConfig(
    api_key="your-api-key",
    api_base="https://api.example.com",
    model="gpt-4",
    headers={"User-Agent": "MyApp/1.0"},
    timeout=30.0,
    max_retries=3,
    retry_delay=1.0
)
```

（目前推荐直接通过 `Chat(api_key, api_base, model, ...)` 显式传参或使用环境变量，详见 `docs/chat.md`）

## 错误处理

### 重试机制

所有客户端都内置了重试机制：

```python
# 配置重试参数
config = HTTPConfig(
    max_retries=5,      # 最大重试次数
    retry_delay=2.0     # 重试延迟（指数退避）
)

client = HTTPClient(config)
```

### 异常处理

```python
import httpx

try:
    response = client.chat_completion(messages=messages)
except httpx.HTTPStatusError as e:
    print(f"HTTP 状态错误: {e.response.status_code}")
    print(f"错误详情: {e.response.text}")
except httpx.RequestError as e:
    print(f"请求错误: {e}")
except Exception as e:
    print(f"其他错误: {e}")
```

## 最佳实践

### 1. 使用上下文管理器

```python
# 推荐：使用上下文管理器自动管理资源
with HTTPClient() as client:
    response = client.get("/api/data")

# 异步版本
async with HTTPClient() as client:
    response = await client.async_get("/api/data")
```

### 2. 配置复用

```python
# 推荐：通过环境变量定义基础参数，代码中按需覆盖
# export OPENAI_API_KEY=...
# export OPENAI_API_BASE=...
chat1 = Chat(model="gpt-4o-mini")
chat2 = Chat(model="gpt-4o-mini", timeout=60)
```

### 3. 异步并发

```python
import asyncio
from chattool import Chat

async def concurrent_requests():
    base = Chat()
    tasks = [
        base.copy().user(f"问题 {i}").async_get_response()
        for i in range(5)
    ]
    responses = await asyncio.gather(*tasks)
    return responses
```

### 4. 参数优化

```python
# 针对不同场景优化参数
creative_config = OpenAIConfig(temperature=0.9, top_p=0.9)
factual_config = OpenAIConfig(temperature=0.1, top_p=0.1)

creative_client = OpenAIClient(creative_config)
factual_client = OpenAIClient(factual_config)
```

## 完整示例

### HTTPClient 完整示例

```python
import asyncio
from chattool.core.request import HTTPClient

async def complete_http_example():
    """HTTPClient 完整使用示例"""
    
    # 1. 创建客户端
    client = HTTPClient(
        api_base="http://localhost:8000",
        timeout=30,
        headers={"User-Agent": "Chattool/1.0"}
    )
    
    try:
        # 2. 同步请求
        print("=== 同步请求 ===")
        response = client.get("/get", params={"test": "sync"})
        print(f"同步响应: {response.json()}")
        
        # 3. 异步请求
        print("\n=== 异步请求 ===")
        response = await client.async_post("/post", data={"test": "async"})
        print(f"异步响应: {response.json()}")
        
        # 4. 自定义请求头
        print("\n=== 自定义请求头 ===")
        response = client.get("/headers", headers={
            "Authorization": "Bearer token123",
            "X-Custom": "value"
        })
        print(f"请求头响应: {response.json()}")
        
    except Exception as e:
        print(f"请求失败: {e}")
    finally:
        # 5. 关闭客户端
        await client.aclose()

# 运行示例
asyncio.run(complete_http_example())
```

### Chat 客户端完整示例

```python
import asyncio
from chattool import Chat

async def complete_chat_example():
    """Chat 客户端完整使用示例"""
    chat = Chat()

    try:
        # 同步聊天
        print("=== 同步聊天 ===")
        response = chat.user("什么是人工智能？").get_response()
        print(f"AI: {response.content}")

        # 异步聊天
        print("\n=== 异步聊天 ===")
        response = await chat.user("什么是机器学习？").async_get_response()
        print(f"AI: {response.content}")

        # 流式响应
        print("\n=== 流式响应 ===")
        print("AI: ", end='')
        async for resp in chat.user("写一首短诗").async_get_response_stream():
            if resp.delta_content:
                print(resp.delta_content, end='', flush=True)
        print()
    except Exception as e:
        print(f"请求失败: {e}")

asyncio.run(complete_chat_example())
```

## 更多示例

查看 `examples/` 目录获取更多使用示例：

- `chat_example.ipynb`: Chat 对象使用示例
