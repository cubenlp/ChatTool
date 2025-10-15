# Chattool 客户端使用指南

## 概述

Chattool 提供了三个核心的 HTTP 客户端类，用于与不同的 API 服务进行交互：

- **HTTPClient**: 通用 HTTP 客户端，提供基础的 HTTP 请求功能
- **OpenAIClient**: OpenAI API 专用客户端，继承自 HTTPClient
- **AzureOpenAIClient**: Azure OpenAI API 专用客户端，继承自 OpenAIClient

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
from chattool.core import HTTPClient, Config

# 使用默认配置
client = HTTPClient()

# 使用自定义配置
config = Config(
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

## OpenAIClient

### 概述

OpenAIClient 是专门用于与 OpenAI API 交互的客户端，继承自 HTTPClient，提供了聊天完成和嵌入等专用功能。

### 初始化

```python
from chattool.core.request import OpenAIClient
from chattool.core.config import OpenAIConfig

# 使用默认配置
client = OpenAIClient()

# 使用自定义配置
config = OpenAIConfig(
    api_key="your-openai-api-key",
    model="gpt-4",
    temperature=0.7,
    max_tokens=1000
)
client = OpenAIClient(config)

# 使用 kwargs 直接设置
client = OpenAIClient(
    api_key="your-api-key",
    model="gpt-4",
    temperature=0.8
)
```

### 聊天完成 API

#### 同步聊天完成

```python
# 基本聊天完成
messages = [
    {"role": "system", "content": "你是一个有用的助手"},
    {"role": "user", "content": "什么是人工智能？"}
]

response = client.chat_completion(
    messages=messages,
    model="gpt-4",
    temperature=0.7,
    max_tokens=500
)

print(response["choices"][0]["message"]["content"])
```

#### 异步聊天完成

```python
import asyncio

async def async_chat_example():
    client = OpenAIClient()
    
    messages = [
        {"role": "user", "content": "解释一下量子计算"}
    ]
    
    response = await client.chat_completion_async(
        messages=messages,
        temperature=0.7
    )
    
    print(response["choices"][0]["message"]["content"])

asyncio.run(async_chat_example())
```

#### 流式聊天完成

```python
import asyncio

async def streaming_chat_example():
    client = OpenAIClient()
    
    messages = [
        {"role": "user", "content": "写一首关于春天的诗"}
    ]
    
    async for chunk in client.chat_completion_stream_async(messages=messages):
        if chunk.get("choices") and chunk["choices"][0].get("delta", {}).get("content"):
            content = chunk["choices"][0]["delta"]["content"]
            print(content, end='', flush=True)
    print()  # 换行

asyncio.run(streaming_chat_example())
```

### 嵌入 API

#### 同步嵌入

```python
# 单个文本嵌入
response = client.embeddings(
    input_text="这是一个测试文本",
    model="text-embedding-ada-002"
)

embeddings = response["data"][0]["embedding"]
print(f"嵌入维度: {len(embeddings)}")

# 批量文本嵌入
texts = ["文本1", "文本2", "文本3"]
response = client.embeddings(
    input_text=texts,
    model="text-embedding-ada-002"
)

for i, item in enumerate(response["data"]):
    print(f"文本 {i+1} 嵌入维度: {len(item['embedding'])}")
```

#### 异步嵌入

```python
import asyncio

async def async_embeddings_example():
    client = OpenAIClient()
    
    response = await client.async_embeddings(
        input_text="异步嵌入测试",
        model="text-embedding-ada-002"
    )
    
    embeddings = response["data"][0]["embedding"]
    print(f"异步嵌入维度: {len(embeddings)}")

asyncio.run(async_embeddings_example())
```

### 参数优先级

OpenAIClient 的参数优先级（从高到低）：
1. 方法调用时传入的参数
2. 配置对象中的参数
3. 默认值

```python
# 配置中设置 temperature=0.5
config = OpenAIConfig(temperature=0.5)
client = OpenAIClient(config)

# 方法调用时的 temperature=0.8 会覆盖配置中的值
response = client.chat_completion(
    messages=messages,
    temperature=0.8  # 这个值会被使用
)
```

## AzureOpenAIClient

### 概述

AzureOpenAIClient 是专门用于与 Azure OpenAI 服务交互的客户端，继承自 OpenAIClient，提供了 Azure 特有的功能。

### 初始化

```python
from chattool.core.request import AzureOpenAIClient
from chattool.core.config import AzureOpenAIConfig

# 使用配置对象
config = AzureOpenAIConfig(
    api_key="your-azure-api-key",
    api_base="https://your-resource.openai.azure.com/",
    api_version="2023-12-01-preview",
    model="gpt-4"
)
client = AzureOpenAIClient(config)

# 使用 kwargs 直接设置
client = AzureOpenAIClient(
    api_key="your-azure-key",
    api_base="https://your-resource.openai.azure.com/",
    api_version="2023-12-01-preview"
)
```

### 自动日志 ID 生成

AzureOpenAIClient 会自动为每个请求生成唯一的日志 ID：

```python
messages = [{"role": "user", "content": "Hello"}]

# 客户端会自动生成日志 ID 并添加到请求头中
response = client.chat_completion(messages=messages)

# 日志 ID 基于消息内容的 MD5 哈希生成
```

### API 版本管理

```python
# 在配置中指定 API 版本
config = AzureOpenAIConfig(
    api_version="2023-12-01-preview"  # 指定版本
)

# 或在初始化时指定
client = AzureOpenAIClient(api_version="2023-12-01-preview")
```

### 聊天完成 API

#### 同步聊天完成

```python
messages = [
    {"role": "system", "content": "你是一个有用的助手"},
    {"role": "user", "content": "什么是 Azure OpenAI？"}
]

response = client.chat_completion(
    messages=messages,
    temperature=0.7,
    max_tokens=500
)

print(response["choices"][0]["message"]["content"])
```

#### 异步聊天完成

```python
import asyncio

async def azure_async_chat():
    client = AzureOpenAIClient()
    
    messages = [
        {"role": "user", "content": "解释一下 Azure 云服务"}
    ]
    
    response = await client.chat_completion_async(
        messages=messages,
        temperature=0.7
    )
    
    print(response["choices"][0]["message"]["content"])

asyncio.run(azure_async_chat())
```

### 嵌入 API

```python
# 同步嵌入
response = client.embeddings(
    input_text="Azure OpenAI 嵌入测试",
    model="text-embedding-ada-002"
)

# 异步嵌入
async def azure_embeddings():
    response = await client.async_embeddings(
        input_text="异步 Azure 嵌入",
        model="text-embedding-ada-002"
    )
    return response

asyncio.run(azure_embeddings())
```

## 配置类

### Config（基础配置）

```python
from chattool.core.config import Config

config = Config(
    api_key="your-api-key",
    api_base="https://api.example.com",
    model="gpt-4",
    headers={"User-Agent": "MyApp/1.0"},
    timeout=30.0,
    max_retries=3,
    retry_delay=1.0
)
```

### OpenAIConfig

```python
from chattool.core.config import OpenAIConfig

config = OpenAIConfig(
    api_key="your-openai-key",
    model="gpt-4",
    temperature=0.7,
    max_tokens=1000,
    top_p=0.9,
    frequency_penalty=0.0,
    presence_penalty=0.0,
    stop=["END"]
)
```

### AzureOpenAIConfig

```python
from chattool.core.config import AzureOpenAIConfig

config = AzureOpenAIConfig(
    api_key="your-azure-key",
    api_base="https://your-resource.openai.azure.com/",
    api_version="2023-12-01-preview",
    model="gpt-4",
    temperature=0.7,
    max_tokens=1000
)
```

## 错误处理

### 重试机制

所有客户端都内置了重试机制：

```python
# 配置重试参数
config = Config(
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
# 推荐：创建配置对象并复用
config = OpenAIConfig(
    model="gpt-4",
    temperature=0.7
)

client1 = OpenAIClient(config)
client2 = OpenAIClient(config)  # 复用配置
```

### 3. 异步并发

```python
import asyncio

async def concurrent_requests():
    client = OpenAIClient()
    
    # 并发执行多个请求
    tasks = [
        client.chat_completion_async(messages=[{"role": "user", "content": f"问题 {i}"}])
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

### OpenAI 客户端完整示例

```python
import asyncio
from chattool.core.request import OpenAIClient
from chattool.core.config import OpenAIConfig

async def complete_openai_example():
    """OpenAI 客户端完整使用示例"""
    
    # 1. 创建配置和客户端
    config = OpenAIConfig(
        model="gpt-4",
        temperature=0.7,
        max_tokens=500
    )
    client = OpenAIClient(config)
    
    try:
        # 2. 同步聊天
        print("=== 同步聊天 ===")
        messages = [{"role": "user", "content": "什么是人工智能？"}]
        response = client.chat_completion(messages=messages)
        print(f"AI: {response['choices'][0]['message']['content']}")
        
        # 3. 异步聊天
        print("\n=== 异步聊天 ===")
        messages = [{"role": "user", "content": "什么是机器学习？"}]
        response = await client.chat_completion_async(messages=messages)
        print(f"AI: {response['choices'][0]['message']['content']}")
        
        # 4. 流式响应
        print("\n=== 流式响应 ===")
        messages = [{"role": "user", "content": "写一首短诗"}]
        print("AI: ", end='')
        async for chunk in client.chat_completion_stream_async(messages=messages):
            if chunk.get("choices") and chunk["choices"][0].get("delta", {}).get("content"):
                print(chunk["choices"][0]["delta"]["content"], end='', flush=True)
        print()
        
        # 5. 嵌入
        print("\n=== 文本嵌入 ===")
        response = await client.async_embeddings(
            input_text="这是一个测试文本",
            model="text-embedding-ada-002"
        )
        print(f"嵌入维度: {len(response['data'][0]['embedding'])}")
        
    except Exception as e:
        print(f"OpenAI 请求失败: {e}")
    finally:
        await client.aclose()

# 运行示例
asyncio.run(complete_openai_example())
```

## 测试

项目包含完整的测试套件，位于 `tests/core/` 目录：

```bash
# 运行所有核心测试
pytest tests/core/

# 运行特定测试文件
pytest tests/core/test_httpclient.py
pytest tests/core/test_oaiclient.py
pytest tests/core/test_azureclient.py

# 运行异步测试
pytest tests/core/ -k "async"
```

## 更多示例

查看 `examples/` 目录获取更多使用示例：

- `httpclient_example.ipynb`: HTTPClient 详细使用示例
- `chat_example.ipynb`: Chat 对象使用示例（包含客户端使用）

这个文档基于实际的示例代码，提供了 Chattool 客户端的全面使用指南，涵盖了从基础 HTTP 请求到高级 AI 功能的所有内容。