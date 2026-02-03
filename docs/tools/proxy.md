# Azure OpenAI 代理服务

ChatTool 提供了一个轻量级的代理服务器，可以将 Azure OpenAI API 转换为标准的 OpenAI API 格式。这使得你可以使用任何支持 OpenAI API 的客户端（如常见的开源软件、SDK 等）来调用 Azure OpenAI 服务。

## 功能特性

- **接口转换**: 将 `/v1/chat/completions` 请求转发到 Azure OpenAI。
- **流式支持**: 完整支持流式 (Streaming) 响应。
- **自动配置**: 自动读取 ChatTool 的 Azure 环境变量配置。

## 快速开始

### 1. 配置 Azure 环境变量

确保你已经配置了 Azure OpenAI 相关的环境变量。你可以通过 `chattool env set` 命令或 `.env` 文件进行配置：

```bash
# 设置 Azure Endpoint
chattool env set AZURE_OPENAI_ENDPOINT="https://your-resource-name.openai.azure.com/"

# 设置 API Key
chattool env set AZURE_OPENAI_API_KEY="your-api-key"

# 设置 API Version (可选，默认使用内置版本)
chattool env set AZURE_OPENAI_API_VERSION="2023-05-15"

# 设置部署的模型名称 (Deployment Name)
chattool env set AZURE_OPENAI_API_MODEL="gpt-35-turbo"
```

### 2. 启动代理服务

使用以下命令启动代理服务器：

```bash
chattool serve proxy
```

默认情况下，服务将在 `http://127.0.0.1:8000` 上监听。

你可以指定主机和端口：

```bash
chattool serve proxy --host 0.0.0.0 --port 8080
```

### 3. 使用 OpenAI 客户端连接

现在，你可以将任何 OpenAI 客户端的 `base_url` 指向本地代理地址。

#### Python 示例 (openai 库)

```python
from openai import OpenAI

client = OpenAI(
    api_key="dummy", # 代理服务会自动使用环境变量中的 Azure Key，这里可以随便填
    base_url="http://127.0.0.1:8000/v1"
)

response = client.chat.completions.create(
    model="gpt-3.5-turbo", # 这里会被代理转发为配置的 Azure Deployment Name
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

#### Curl 示例

```bash
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```
