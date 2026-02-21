# ChatTool 客户端命令行工具文档

ChatTool 提供了两个主要的命令行工具：`chattool` 用于各种服务管理，`chatenv` 用于环境配置管理。

## 命令结构

### chattool

CLI按功能分为几个命令组：

- **`dns`**: DNS 记录管理和动态 DNS (DDNS) 工具。
- **`serve`**: 本地服务器实用工具（例如，请求捕获）。
- **`client`**: 远程服务客户端工具。
- **`mcp`**: 模型上下文协议 (MCP) 服务器管理。
- **`kb`**: 知识库 (Knowledge Base) 管理工具。

### chatenv

独立的配置和环境变量管理工具：

- **`init`**: 初始化配置。
- **`set/get/unset`**: 管理单个配置项。
- **`list`**: 管理多环境配置。
- **`cat`**: 查看配置内容。

---

## 1. DNS 管理 (`dns`)

管理 DNS 记录并自动更新动态 DNS。支持阿里云 (Aliyun) 和腾讯云 (Tencent) DNS 提供商。

### 1.1 动态 DNS (DDNS)

使用当前 IP 地址更新 DNS 记录。支持公网 (Public) 和局域网 (Local) IP，以及持续监控模式。

```bash
# 更新域名的公网 IP (一次性)
chattool dns ddns public.example.com

# 以监控模式运行 (每 120 秒检查一次)
chattool dns ddns public.example.com --monitor

# 更新局域网 IP，并指定子网过滤器
chattool dns ddns local.example.com --ip-type local --local-ip-cidr 192.168.1.0/24

# 指定 TTL 和重试参数
chattool dns ddns public.example.com --ttl 600 --max-retries 5 --retry-delay 10
```

**完整选项说明:**
- `full_domain`: 完整域名 (例如 `sub.example.com`)。
- `-d, --domain`: 域名 (例如 `example.com`)。
- `-r, --rr`: 主机记录 (例如 `sub`)。
- `--monitor`: 启用持续监控模式。
- `-i, --interval`: 检查间隔，单位为秒 (默认: 120)。
- `--ip-type`: 更新的 IP 类型: `public` (默认) 或 `local`。
- `--local-ip-cidr`: 局域网 IP 过滤网段 (例如 `192.168.0.0/16`)，仅当 `--ip-type=local` 时有效。
- `-p, --provider`: DNS 提供商: `aliyun` (默认) 或 `tencent`。
- `--ttl`: TTL 值 (默认: 600)。
- `--max-retries`: 最大重试次数 (默认: 3)。
- `--retry-delay`: 重试延迟秒数 (默认: 5)。
- `--log-file`: 日志文件路径 (默认不记录到文件，除非开启监控模式且未指定则使用默认)。
- `--log-level`: 日志级别 (默认: INFO)。

### 1.2 记录管理

**获取记录 (`get`):**
```bash
# 获取域名的所有记录
chattool dns get -d example.com

# 获取特定记录
chattool dns get test.example.com
```
**选项:**
- `-t, --type`: 记录类型过滤 (例如 `A`, `TXT`, `CNAME`)。
- `-p, --provider`: DNS 提供商 (默认: `aliyun`)。

**设置/更新记录 (`set`):**
```bash
# 设置 A 记录
chattool dns set test.example.com -v 1.2.3.4

# 设置 TXT 记录
chattool dns set -d example.com -r _test -t TXT -v "some-value"
```
**选项:**
- `-v, --value`: 记录值 (必填)。
- `-t, --type`: 记录类型 (默认: `A`)。
- `--ttl`: TTL 值 (默认: 600)。
- `-p, --provider`: DNS 提供商 (默认: `aliyun`)。

### 1.3 SSL 证书 (`cert-update`)

使用 Let's Encrypt 和 DNS 验证自动申请和续期 SSL 证书。

```bash
chattool dns cert-update -d example.com -d *.example.com -e admin@example.com
```

**输出文件结构:**
证书将保存在 `<cert-dir>/<domain>/` 目录下，包含以下文件：
- `fullchain.pem`: 完整证书链 (适用于 Nginx/Apache 配置)。
- `privkey.pem`: 私钥文件 (适用于 Nginx/Apache 配置)。
- `cert.pem`: 叶子证书。
- `chain.pem`: 中间证书。

**完整选项说明:**
- `-d, --domains`: 域名列表 (可多次使用，支持通配符)。
- `-e, --email`: 用于 Let's Encrypt 注册的邮箱。
- `-p, --provider`: 用于验证的 DNS 提供商 (`aliyun` 或 `tencent`，默认: `aliyun`)。
- `--cert-dir`: 证书存储根目录 (默认: `certs`)。
- `--staging`: 使用 Let's Encrypt 测试环境 (用于测试)。
- `--log-file`: 日志文件路径 (默认不记录到文件)。

---

## 2. 远程客户端工具 (`client`)

### 2.1 SSL 证书客户端 (`client cert`)

用于与 `chattool serve cert` 服务交互的客户端工具，支持申请、查询和下载证书。

**全局选项:**
- `--server`: 服务地址 (默认: `http://127.0.0.1:8000`)
- `--token`: 鉴权 Token (也可通过 `CHATTOOL_CERT_TOKEN` 环境变量设置)

#### 申请证书 (`apply`)
```bash
chattool client cert apply -d example.com -d *.example.com --token my-secret-token
```
**选项:**
- `-d, --domain`: 域名列表 (必填)。
- `-e, --email`: 邮箱 (如果配置了 `git config user.email` 则可选，否则必填)。
- `-p, --provider`: DNS 提供商 (可选)。
- `--secret-id/--secret-key`: 云厂商凭证 (可选)。

#### 查看证书列表 (`list`)
```bash
chattool client cert list --token my-secret-token
```
列出当前 Token 下申请的所有证书及其有效期信息。

#### 下载证书 (`download`)
```bash
chattool client cert download example.com -o ./my-certs --token my-secret-token
```
下载指定域名的证书文件 (`cert.pem`, `privkey.pem`, `fullchain.pem`) 到本地目录。

---

## 3. 环境管理 (`env`)

管理存储在 `.env` 文件中的全局配置和环境变量。

```bash
# 交互式初始化或更新配置
chattool env init -i

# 列出所有配置
chattool env list

# 设置配置值
chattool env set CHATTOOL_DNS_PROVIDER=tencent

# 获取配置值
chattool env get CHATTOOL_DNS_PROVIDER

# 删除配置值
chattool env unset CHATTOOL_DNS_PROVIDER
```

**命令详解:**
- `init`: 初始化或更新配置文件。使用 `-i, --interactive` 进入交互模式。
- `list`: 列出所有当前生效的配置值。
- `set`: 设置单个配置项，格式为 `KEY=VALUE`。
- `get`: 获取单个配置项的值。
- `unset`: 删除（置空）单个配置项的值。

---

## 4. 本地服务器工具 (`serve`)

### 4.1 请求捕获 (`capture`)

启动一个本地 HTTP 服务器，捕获并记录所有传入的请求。常用于调试 Webhook 或检查 API 调用。

```bash
# 在默认端口 (8000) 启动捕获服务器
chattool serve capture

# 后台运行并启用自动重载
chattool serve capture --host 0.0.0.0 --port 8080 --daemon --reload
```

**服务器功能:**
- 详细记录请求头 (Headers)、查询参数 (Query Params) 和请求体 (Body)。
- 自动生成用于复现请求的 `curl` 命令。
- 在 `/docs` 提供 Web 文档界面。

**选项说明:**
- `--host`: 监听地址 (默认: `0.0.0.0`)。
- `--port`: 监听端口 (默认: `8000`)。
- `-d, --daemon`: 后台运行模式（使用线程）。
- `--reload`: 启用自动重载（开发模式）。

### 4.2 SSL 证书服务 (`cert`)

启动一个 REST API 服务，提供 SSL 证书的异步申请和安全下载功能。支持多租户隔离，使用 Token 进行鉴权和数据隔离。

```bash
# 启动服务，监听 8000 端口，证书存储在 ./certs
chattool serve cert --provider aliyun

# 指定监听地址、端口和输出目录
chattool serve cert --host 0.0.0.0 --port 8080 --output ./my-certs
```

**核心特性:**
- **Token 隔离**: 使用请求 Header 中的 Token 的哈希值作为子目录名，实现多租户物理隔离。不同 Token 无法访问彼此的数据。
- **异步申请**: 提交申请后立即返回，后台执行 ACME 验证流程。
- **元数据管理**: 自动记录证书的生成时间、过期时间和剩余天数，支持列表查询。

**API 接口 (需在 Header 中携带 `X-ChatTool-Token`):**

1.  **申请证书**: `POST /cert/apply`
    *   Body:
        ```json
        {
          "domains": ["example.com", "*.example.com"],
          "email": "admin@example.com",
          "provider": "aliyun",
          "secret_id": "...",
          "secret_key": "..."
        }
        ```
    *   Response: `{"status": "pending", "message": "..."}`

2.  **获取证书列表**: `GET /cert/list`
    *   返回该 Token 下所有已生成的证书信息（包含有效期、路径等）。
    *   Response:
        ```json
        [
          {
            "domain": "example.com",
            "created_at": "2023-10-27T10:00:00",
            "expires_at": "2024-01-25T10:00:00",
            "days_remaining": 89,
            "cert_path": "example.com/cert.pem",
            ...
          }
        ]
        ```

3.  **下载证书**: `GET /cert/download/{domain}/{filename}`
    *   `domain`: 主域名 (如 `example.com`)
    *   `filename`: 文件名 (如 `fullchain.pem`)

**选项说明:**
- `--host`: 监听地址 (默认: `0.0.0.0`)。
- `-p, --port`: 监听端口 (默认: `8000`)。
- `-o, --output`: 证书存储根目录 (默认: `certs`)。
- `--provider`: 默认 DNS 提供商 (`aliyun` 或 `tencent`)。
- `--secret-id`: 默认云厂商 Secret ID (可选)。
- `--secret-key`: 默认云厂商 Secret Key (可选)。

---

## 5. MCP 服务器 (`mcp`)

管理 ChatTool 模型上下文协议 (MCP) 服务器。

```bash
# 运行 MCP 服务器 (标准输入输出模式，默认)
chattool mcp start

# 运行 MCP 服务器 (HTTP 模式)
chattool mcp start --transport http --port 8000

# 查看服务器能力信息
chattool mcp info
```

**选项说明 (`start`):**
- `-t, --transport`: 传输模式，可选 `stdio` (默认) 或 `http`。
- `--host`: HTTP 服务器主机地址 (默认: `127.0.0.1`)。
- `--port`: HTTP 服务器端口 (默认: `8000`)。

---

## 6. 知识库管理 (`kb`)

管理基于 Zulip 的知识库工作区。支持消息同步、搜索、导出及处理。

### 基本用法

```bash
# 初始化工作区
chattool kb init [name]

# 跟踪 Zulip Stream
chattool kb track [name] "general"

# 同步消息 (快照模式，获取最新消息)
chattool kb sync [name] --latest --limit 100

# 列出主题
chattool kb list [name] --stream "general"

# 显示特定主题的消息
chattool kb show [name] "general" "welcome"
```

### 命令详解

**`init`**: 初始化一个新的知识库工作区。
- `name`: 工作区名称（可选，默认使用 Zulip 站点名）。

**`track` / `untrack`**: 跟踪或取消跟踪 Zulip 中的 Stream。
- `name`: 工作区名称。
- `stream`: Stream 名称。

**`sync`**: 同步已跟踪 Stream 的消息。
- `name`: 工作区名称。
- `--latest`: 仅获取最新消息（快照模式）。
- `--limit`: 获取消息的最大数量 (默认: 1000)。

**`list`**: 列出工作区中的主题。
- `name`: 工作区名称。
- `--stream`: 按 Stream 过滤。
- `--export`: 导出结果到 CSV 文件。

**`show`**: 显示特定主题的消息内容。
- `name`: 工作区名称。
- `stream`: Stream 名称。
- `topic`: Topic 名称。
- `--limit`: 显示消息数量 (默认: 50)。
- `--export`: 导出消息到 TXT 文件。

**`search`**: 全文搜索知识库消息。
- `name`: 工作区名称。
- `query`: 搜索关键词。

**`process`**: 处理主题内容并重新发布（演示功能）。
- `name`: 工作区名称。
- `stream`: 源 Stream。
- `topic`: 源 Topic。
- `--to-stream`: 目标 Stream。
- `--to-topic`: 目标 Topic。
