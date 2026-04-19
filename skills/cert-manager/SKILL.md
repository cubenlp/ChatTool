---
name: cert-manager
description: "Generate and manage SSL/TLS certificates automatically using DNS validation via Let's Encrypt. Use when the user asks to create, renew, or manage SSL certificates, set up HTTPS, configure Let's Encrypt, or automate certificate issuance for a domain."
version: 0.1.0
---

# Cert Manager

Automate SSL certificate generation and renewal using DNS validation (Let's Encrypt) via four integration routes.

## Route Selection

| Route | Best For | Entry Point |
| :--- | :--- | :--- |
| **Code Import** | Python scripts, app integration | `chattool.tools.cert.cert_updater.SSLCertUpdater` |
| **CLI** | Shell scripts, local machine ops | `chattool dns cert-update` |
| **Server-Client** | Remote management, distributed / multi-tenant | `chattool serve cert` + `chattool client cert` |
| **MCP** | AI agent tool calls | `dns_cert_update` (MCP tool) |

## Route 1: Code Import

```python
import asyncio
from chattool.tools.cert.cert_updater import SSLCertUpdater

async def main():
    updater = SSLCertUpdater(
        domains=["example.com", "*.example.com"],
        email="admin@example.com",
        dns_type="aliyun",
        cert_dir="./certs",
        access_key_id="...",       # or set via env var
        access_key_secret="..."    # or set via env var
    )
    success = await updater.run_once()

asyncio.run(main())
```

**Required env vars (Aliyun)**: `ALIBABA_CLOUD_ACCESS_KEY_ID`, `ALIBABA_CLOUD_ACCESS_KEY_SECRET`

## Route 2: CLI

```bash
chattool dns cert-update \
    -d example.com -d "*.example.com" \
    -e admin@example.com \
    --provider aliyun \
    --cert-dir ./my-certs
```

## Route 3: Server-Client

**Start server** (with auth token):
```bash
chattool serve cert --token "my-secret-token" --provider aliyun
```

**Client operations**:
```bash
# Request certificate
chattool client cert apply \
    -d example.com -d "*.example.com" \
    --token "my-secret-token" \
    --server http://<server-ip>:8000

# List certificates
chattool client cert list --token "my-secret-token" --server http://<server-ip>:8000

# Download certificate
chattool client cert download example.com --token "my-secret-token" --server http://<server-ip>:8000
```

## Route 4: MCP Protocol

**Tool name**: `dns_cert_update`

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

**Supported providers**: `aliyun`, `tencent`
