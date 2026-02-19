---
name: cert-manager
description: 一个使用 DNS 验证（Let's Encrypt）进行自动化 SSL 证书生成和管理的综合工具集。该技能支持多种使用途径，包括直接代码导入、命令行界面（CLI）、客户端-服务器架构和 MCP 协议集成。
---

# Cert Manager Skill (证书管理技能)

## 描述

本技能提供使用 DNS 验证（Let's Encrypt）的自动化 SSL 证书生成和管理功能。它通过多种使用途径提供灵活性，允许您根据具体的开发或部署场景选择最佳方法。

## 使用途径

根据您的场景选择最合适的途径：

| 途径 | 场景 | 核心工具 |
| :--- | :--- | :--- |
| **1. 代码导入** | Python 脚本开发，集成到其他应用中 | `chattool.tools.cert.cert_updater.SSLCertUpdater` |
| **2. CLI** | 本地机器，Shell 脚本自动化，简单运维 | `chattool dns cert-update` |
| **3. 服务器-客户端** | 远程管理，异步任务，多租户，分布式 | `chattool serve cert` (Server) <br> `chattool client cert` (Client) |
| **4. MCP** | AI Agent 集成，通用工具调用 | `dns_cert_update` (通过 MCP Server) |

---

## 详细说明

### 途径 1: 代码导入

在 Python 代码中直接导入并使用 `SSLCertUpdater` 类。

**配置**:
- 配置 DNS 提供商 AccessKey/SecretKey（通过环境变量或参数）。

**示例**:
```python
import asyncio
from chattool.tools.cert.cert_updater import SSLCertUpdater
from chattool.utils import setup_logger

async def main():
    updater = SSLCertUpdater(
        domains=["example.com", "*.example.com"],
        email="admin@example.com",
        dns_type="aliyun",
        cert_dir="./certs",
        access_key_id="...",      # 可选，默认为环境变量
        access_key_secret="..."   # 可选，默认为环境变量
    )
    success = await updater.run_once()
    if success:
        print("Certificate generated successfully!")

if __name__ == "__main__":
    asyncio.run(main())
```

### 途径 2: CLI

使用 `chattool` 命令行界面直接请求证书。

**配置**:
- 设置环境变量 `ALIBABA_CLOUD_ACCESS_KEY_ID` 和 `ALIBABA_CLOUD_ACCESS_KEY_SECRET`（针对阿里云）。

**示例**:
```bash
# 生成证书
chattool dns cert-update \
    -d example.com -d "*.example.com" \
    -e admin@example.com \
    --provider aliyun \
    --cert-dir ./my-certs
```

### 途径 3: 服务器-客户端

启动 HTTP 服务器处理证书请求，并通过客户端工具远程调用。支持多租户隔离（基于 Token）。

**步骤 1: 启动服务器**
```bash
# 在服务器启动，设置认证 token
chattool serve cert --token "my-secret-token" --provider aliyun
```

**步骤 2: 客户端调用**
```bash
# 申请证书（客户端）
chattool client cert apply \
    -d example.com -d "*.example.com" \
    --token "my-secret-token" \
    --server http://<server-ip>:8000

# 列出证书
chattool client cert list --token "my-secret-token" --server http://<server-ip>:8000

# 下载证书
chattool client cert download example.com --token "my-secret-token" --server http://<server-ip>:8000
```

### 途径 4: MCP 协议

如果 ChatTool MCP Server 正在运行，则通过 MCP 协议调用工具。

**工具名称**: `dns_cert_update`

**参数**:
- `domains`: List[str] (例如 `["example.com"]`)
- `email`: str
- `provider`: str ("aliyun" 或 "tencent")

**示例 (JSON-RPC)**:
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "dns_cert_update",
    "arguments": {
      "domains": ["example.com"],
      "email": "admin@example.com",
      "provider": "aliyun"
    }
  },
  "id": 1
}
```
