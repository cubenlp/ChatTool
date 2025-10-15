# Chattool 核心模块文档

## 概述

Chattool 核心模块提供了三个主要的 HTTP 客户端类，用于与不同的 API 服务进行交互：

- **HTTPClient**: 基础HTTP客户端，提供通用的HTTP请求功能
- **OpenAIClient**: OpenAI API 专用客户端，继承自 HTTPClient
- **AzureOpenAIClient**: Azure OpenAI API 专用客户端，继承自 OpenAIClient

## HTTPClient

### 概述

HTTPClient 是基础的 HTTP 客户端类，提供了同步和异步的HTTP请求功能，支持重试机制、超时设置和连接管理。

### 初始化

```python
from chattool.core import HTTPClient, Config

# 使用默认配置
client = HTTPClient()

# 使用自定义配置
config = Config(
    api_base="https://api.example.com",
    timeout=30,
    max_retries=3,
    retry_delay=1
)
client = HTTPClient(config)

# 使用kwargs直接设置参数
client = HTTPClient(
    api_base="https://api.example.com",
    timeout=30,
    custom_header="value"
)
```

### 主要方法

#### 同步请求方法

```python
# 通用请求方法
response = client.request(
    method="GET",
    endpoint="/api/data",
    data={"key": "value"},
    params={"page": 1},
    headers={"Authorization": "Bearer token"}
)

# 便捷方法
response = client.get("/api/data", params={"page": 1})
response = client.post("/api/data", data={"key": "value"})
response = client.put("/api/data", data={"key": "value"})
response = client.delete("/api/data")
```

#### 异步请求方法

```python
import asyncio

async def main():
    # 通用异步请求方法
    response = await client.async_request(
        method="GET",
        endpoint="/api/data",
        data={"key": "value"}
    )
    
    # 异步便捷方法
    response = await client.async_get("/api/data")
    response = await client.async_post("/api/data", data={"key": "value"})
    response = await client.async_put("/api/data", data={"key": "value"})
    response = await client.async_delete("/api/data")

asyncio.run(main())
```

### 上下文管理器

```python
# 同步上下文管理器
with HTTPClient(config) as client:
    response = client.get("/api/data")

# 异步上下文管理器
async with HTTPClient(config) as client:
    response = await client.async_get("/api/data")
```

### 特性

- **自动重试**: 支持指数退避的重试机制
- **连接池**: 自动管理HTTP连接池
- **超时控制**: 可配置的请求超时
- **错误处理**: 自动处理HTTP状态错误
- **懒加载**: 客户端实例按需创建

## OpenAIClient

### 概述
OpenAIClient 继承自 HTTPClient，专门用于与 OpenAI API 进行交互，提供了聊天完成和嵌入等功能。

### 初始化

```python
from chattool.core import OpenAIClient, OpenAIConfig

# 使用默认配置（从环境变量读取）
client = OpenAIClient()

# 使用自定义配置
config = OpenAIConfig(
    api_key="your-api-key",
    api_base="https://api.openai.com/v1",
    model="gpt-3.5-turbo",
    temperature=0.7,
    max_tokens=1000
)
client = OpenAIClient(config)
```

### 聊天完成 API

#### 同步调用

```python
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello, how are you?"}
]

# 基础调用
response = client.chat_completion(messages)

# 带参数调用
response = client.chat_completion(
    messages,
    model="gpt-4",
    temperature=0.5,
    max_tokens=500,
    top_p=0.9
)

print(response["choices"][0]["message"]["content"])
```

#### 异步调用

```python
async def chat_example():
    messages = [
        {"role": "user", "content": "What is Python?"}
    ]
    
    response = await client.async_chat_completion(
        messages,
        model="gpt-3.5-turbo",
        temperature=0.3
    )
    
    return response["choices"][0]["message"]["content"]

result = asyncio.run(chat_example())
```

### 嵌入 API

#### 同步调用

```python
# 单个文本嵌入
response = client.embeddings("Hello world")

# 批量文本嵌入
texts = ["Hello world", "How are you?", "Python is great"]
response = client.embeddings(texts, model="text-embedding-ada-002")

embeddings = [item["embedding"] for item in response["data"]]
```

#### 异步调用

```python
async def embedding_example():
    response = await client.async_embeddings(
        ["Text 1", "Text 2"],
        model="text-embedding-ada-002"
    )
    return response["data"]

embeddings = asyncio.run(embedding_example())
```

### 参数优先级

OpenAIClient 支持多层参数配置，优先级如下：
1. 方法调用时的 kwargs 参数（最高优先级）
2. 配置对象中的参数
3. 默认值（最低优先级）

```python
# 配置中设置默认值
config = OpenAIConfig(temperature=0.7, model="gpt-3.5-turbo")
client = OpenAIClient(config)

# 调用时覆盖配置
response = client.chat_completion(
    messages,
    temperature=0.2,  # 覆盖配置中的 0.7
    model="gpt-4"     # 覆盖配置中的 gpt-3.5-turbo
)
```

## AzureOpenAIClient

### 概述
AzureOpenAIClient 继承自 OpenAIClient，专门用于与 Azure OpenAI 服务进行交互，包含 Azure 特有的认证和请求处理逻辑。

### 初始化

```python
from chattool.core import AzureOpenAIClient, AzureOpenAIConfig

# 使用自定义配置
config = AzureOpenAIConfig(
    api_key="your-azure-api-key",
    api_base="https://your-resource.openai.azure.com/openai/deployments/your-deployment",
    api_version="2024-02-15-preview",
    model="gpt-35-turbo",
    temperature=0.7
)
client = AzureOpenAIClient(config)
```

### Azure 特有功能

#### 自动日志ID生成

Azure 客户端会自动为每个请求生成唯一的日志ID：

```python
messages = [{"role": "user", "content": "Hello"}]

# 客户端会自动添加 X-TT-LOGID 请求头
response = client.chat_completion(messages)
```

#### API 版本管理

```python
# 在配置中设置 API 版本
config = AzureOpenAIConfig(
    api_version="2024-02-15-preview"
)

# 或在请求时指定参数
response = client.chat_completion(
    messages,
    params={"api-version": "2024-02-15-preview"}
)
```

### 聊天完成 API

#### 同步调用

```python
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello from Azure!"}
]

# Azure 特有的调用方式
response = client.chat_completion(
    messages,
    model="gpt-35-turbo",  # Azure 部署名称
    temperature=0.7,
    uri="",  # Azure 使用空字符串，因为 api_base 已包含完整路径
    params={"api-version": "2024-02-15-preview"}
)
```

#### 异步调用

```python
async def azure_chat_example():
    messages = [{"role": "user", "content": "What is Azure OpenAI?"}]
    
    response = await client.async_chat_completion(
        messages,
        model="gpt-4",
        temperature=0.3,
        uri=""
    )
    
    return response["choices"][0]["message"]["content"]

result = asyncio.run(azure_chat_example())
```

### 嵌入 API

```python
# Azure 嵌入 API
response = await client.async_embeddings(
    ["Azure OpenAI text"],
    model="text-embedding-ada-002",
    uri="",  # 使用配置中的完整路径
    params={"api-version": "2024-02-15-preview"}
)
```

## 配置管理

### Config 类

基础配置类，用于 HTTPClient：

```python
from chattool.core.config import Config

config = Config(
    api_base="https://api.example.com",
    headers={"User-Agent": "MyApp/1.0"},
    timeout=30,
    max_retries=3,
    retry_delay=1
)
```

### OpenAIConfig 类

OpenAI 专用配置类：

```python
from chattool.core.config import OpenAIConfig

config = OpenAIConfig(
    api_key="sk-...",
    api_base="https://api.openai.com/v1",
    model="gpt-3.5-turbo",
    temperature=0.7,
    max_tokens=1000,
    top_p=1.0,
    frequency_penalty=0.0,
    presence_penalty=0.0
)
```

### AzureOpenAIConfig 类

Azure OpenAI 专用配置类：

```python
from chattool.core.config import AzureOpenAIConfig

config = AzureOpenAIConfig(
    api_key="your-azure-key",
    api_base="https://your-resource.openai.azure.com/openai/deployments/your-deployment",
    api_version="2024-02-15-preview",
    model="gpt-35-turbo",
    temperature=0.7
)
```

## 错误处理

### 重试机制

所有客户端都支持自动重试：

```python
config = Config(
    max_retries=3,      # 最大重试次数
    retry_delay=1       # 基础延迟时间（秒）
)

# 重试使用指数退避：1s, 2s, 4s, 8s...
client = HTTPClient(config)
```

### 异常处理

```python
import httpx
from chattool.core import OpenAIClient

client = OpenAIClient()

try:
    response = client.chat_completion(messages)
except httpx.HTTPStatusError as e:
    print(f"HTTP错误: {e.response.status_code}")
except httpx.RequestError as e:
    print(f"请求错误: {e}")
except Exception as e:
    print(f"其他错误: {e}")
```

## 最佳实践

### 1. 使用上下文管理器

```python
# 推荐：自动管理连接
async with OpenAIClient(config) as client:
    response = await client.async_chat_completion(messages)

# 或者手动关闭
client = OpenAIClient(config)
try:
    response = client.chat_completion(messages)
finally:
    client.close()
```

### 2. 配置复用

```python
# 创建可复用的配置
config = OpenAIConfig(
    model="gpt-3.5-turbo",
    temperature=0.7,
    max_tokens=1000
)

# 在多个地方使用相同配置
client1 = OpenAIClient(config)
client2 = OpenAIClient(config)
```

### 3. 异步并发

```python
import asyncio

async def process_multiple_requests():
    async with OpenAIClient(config) as client:
        tasks = []
        for message_set in message_sets:
            task = client.async_chat_completion(message_set)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results
```

### 4. 参数优化

```python
# 针对不同场景优化参数
creative_config = OpenAIConfig(temperature=0.9, top_p=0.9)
factual_config = OpenAIConfig(temperature=0.1, top_p=0.1)

creative_client = OpenAIClient(creative_config)
factual_client = OpenAIClient(factual_config)
```

## 测试

项目包含完整的测试套件，位于 `tests/core/` 目录：

- `test_httpclient.py`: HTTPClient 测试
- `test_oaiclient.py`: OpenAIClient 测试  
- `test_azureclient.py`: AzureOpenAIClient 测试

运行测试：

```bash
# 运行所有核心测试
pytest tests/core/

# 运行特定测试文件
pytest tests/core/test_httpclient.py
pytest tests/core/test_oaiclient.py
pytest tests/core/test_azureclient.py
```

## 更多示例

查看 `examples/` 目录获取更多使用示例：

- `http_client_example.py`: HTTPClient 使用示例
- `openai_client_example.py`: OpenAI 客户端示例
- `azure_client_example.py`: Azure OpenAI 客户端示例