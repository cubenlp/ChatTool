---
name: cert-manager
description: "通过 Let's Encrypt 的 DNS 验证自动生成和管理 SSL/TLS 证书。用户提到创建、续期、管理 SSL 证书，配置 HTTPS，设置 Let's Encrypt，或自动化签发某个域名证书时使用。"
version: 0.1.0
---

# Cert Manager

通过四种集成方式，自动化完成基于 DNS 验证的 SSL 证书申请与续期。

## 路线选择

| 路线 | 适用场景 | 入口 |
| :--- | :--- | :--- |
| **代码导入** | Python 脚本、应用内集成 | `chattool.tools.cert.cert_updater.SSLCertUpdater` |
| **CLI** | Shell 脚本、本地运维 | `chattool dns cert-update` |
| **Server-Client** | 远程管理、分布式、多租户 | `chattool serve cert` + `chattool client cert` |
| **MCP** | AI agent 工具调用 | `dns_cert_update` |

## 路线 1：代码导入

```python
import asyncio
from chattool.tools.cert.cert_updater import SSLCertUpdater

async def main():
    updater = SSLCertUpdater(
        domains=["example.com", "*.example.com"],
        email="admin@example.com",
        dns_type="aliyun",
        cert_dir="./certs",
        access_key_id="...",       # 或通过环境变量提供
        access_key_secret="..."    # 或通过环境变量提供
    )
    success = await updater.run_once()

asyncio.run(main())
```

**阿里云必需环境变量**：`ALIBABA_CLOUD_ACCESS_KEY_ID`、`ALIBABA_CLOUD_ACCESS_KEY_SECRET`

## 路线 2：CLI

```bash
chattool dns cert-update \
    -d example.com -d "*.example.com" \
    -e admin@example.com \
    --provider aliyun \
    --cert-dir ./my-certs
```

## 路线 3：Server-Client

**启动服务端**：
```bash
chattool serve cert --token "my-secret-token" --provider aliyun
```

**客户端操作**：
```bash
# 申请证书
chattool client cert apply \
    -d example.com -d "*.example.com" \
    --token "my-secret-token" \
    --server http://<server-ip>:8000

# 列出证书
chattool client cert list --token "my-secret-token" --server http://<server-ip>:8000

# 下载证书
chattool client cert download example.com --token "my-secret-token" --server http://<server-ip>:8000
```

## 路线 4：MCP

**工具名**：`dns_cert_update`

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

**支持的 provider**：`aliyun`、`tencent`
