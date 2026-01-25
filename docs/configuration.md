# 配置管理指南

ChatTool 从 v4.3.0 开始引入了全新的集中式配置管理系统，支持从 `.env` 文件自动加载配置，并提供了类型安全的代码内访问方式。

## 配置机制

ChatTool 使用 `dotenv` 加载环境变量，配置加载顺序如下（优先级从高到低）：

1. **运行时显式设置**：在代码中通过 `BaseEnvConfig.set()` 动态修改的值。
2. **`.env` 文件**：项目根目录或配置目录下的 `.env` 文件。
3. **系统环境变量**：操作系统层面的环境变量（如 `export OPENAI_API_KEY=...`）。
4. **默认值**：代码中定义的默认值。

## 快速开始

### 1. 生成配置模板

在项目根目录下运行以下 Python 代码，生成包含所有可用配置项的 `.env` 模板文件：

```python
from chattool import create_env_file

# 生成 .env 文件
create_env_file(".env")
```

### 2. 编辑配置文件

打开生成的 `.env` 文件，填入你的密钥和配置：

```bash
# ==================== OpenAI Configuration ====================
OPENAI_API_KEY='sk-xxxxxxxxxxxx'
OPENAI_API_BASE='https://api.openai.com/v1'

# ==================== Alibaba Cloud (Aliyun) Configuration ====================
ALIBABA_CLOUD_ACCESS_KEY_ID='LTAIxxxxxxxx'
ALIBABA_CLOUD_ACCESS_KEY_SECRET='xxxxxxxxxxxx'
```

### 3. 代码中使用

在代码中，你不再需要手动读取 `os.getenv`，ChatTool 的各个组件会自动读取配置。

```python
from chattool import Chat

# 自动读取 OPENAI_API_KEY 等配置
chat = Chat() 
```

## 高级用法

### 动态修改配置

你可以在运行时动态修改配置，这对多账号切换或测试场景非常有用。修改后，**新创建**的客户端实例将使用新配置。

```python
from chattool.utils.config import BaseEnvConfig, OpenAIConfig
from chattool import Chat

# 查看当前配置
print(OpenAIConfig.OPENAI_API_KEY.value)

# 动态修改 API Key
BaseEnvConfig.set("OPENAI_API_KEY", "new-secret-key")

# 新的 Chat 实例将使用新 Key
chat = Chat()
print(chat.api_key) # 输出: new-secret-key
```

### 访问配置值

你可以直接从配置类中访问当前生效的配置值：

```python
from chattool.utils.config import OpenAIConfig, AliyunConfig

key = OpenAIConfig.OPENAI_API_KEY.value
region = AliyunConfig.ALIBABA_CLOUD_REGION_ID.value
```

### 敏感信息保护

配置系统会自动识别敏感字段（如 API Key、Secret），在打印配置或生成日志时自动进行脱敏处理（用 `*` 代替）。

```python
from chattool.utils.config import BaseEnvConfig

# 打印当前所有配置（敏感信息已脱敏）
BaseEnvConfig.print_config()
```

## 支持的配置项

目前支持以下服务的配置：

- **OpenAI**: `OPENAI_API_KEY`, `OPENAI_API_BASE` 等
- **Azure OpenAI**: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT` 等
- **阿里云**: `ALIBABA_CLOUD_ACCESS_KEY_ID`, `ALIBABA_CLOUD_ACCESS_KEY_SECRET` 等
- **腾讯云**: `TENCENT_SECRET_ID`, `TENCENT_SECRET_KEY` 等
- **Zulip**: `ZULIP_BOT_EMAIL`, `ZULIP_BOT_API_KEY` 等
