---
name: cert-manager
description: A comprehensive toolset for automated SSL certificate generation and management using DNS validation (Let's Encrypt). This skill supports multiple usage routes including direct code import, command-line interface (CLI), client-server architecture, and MCP protocol integration.
---

# Cert Manager Skill

## Description

This skill provides automated SSL certificate generation and management capabilities using DNS validation (Let's Encrypt). It offers flexibility through multiple usage routes, allowing you to choose the best method for your specific development or deployment scenario.

## Usage Routes

Choose the most appropriate route based on your scenario:

| Route | Scenario | Core Tool |
| :--- | :--- | :--- |
| **1. Code Import** | Python script development, integration into other apps | `chattool.tools.cert.cert_updater.SSLCertUpdater` |
| **2. CLI** | Local machine, Shell script automation, simple ops | `chattool dns cert-update` |
| **3. Server-Client** | Remote management, async tasks, multi-tenant, distributed | `chattool serve cert` (Server) <br> `chattool client cert` (Client) |
| **4. MCP** | AI Agent integration, generic tool call | `dns_cert_update` (via MCP Server) |

---

## Detailed Instructions

### Route 1: Code Import

Import and use the `SSLCertUpdater` class directly in Python code.

**Configuration**:
- Configure DNS Provider AccessKey/SecretKey (via env vars or args).

**Example**:
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
        access_key_id="...",      # Optional, defaults to env var
        access_key_secret="..."   # Optional, defaults to env var
    )
    success = await updater.run_once()
    if success:
        print("Certificate generated successfully!")

if __name__ == "__main__":
    asyncio.run(main())
```

### Route 2: CLI

Use the `chattool` command-line interface to request certificates directly.

**Configuration**:
- Set env vars `ALIBABA_CLOUD_ACCESS_KEY_ID` and `ALIBABA_CLOUD_ACCESS_KEY_SECRET` (for Aliyun).

**Example**:
```bash
# Generate certificate
chattool dns cert-update \
    -d example.com -d "*.example.com" \
    -e admin@example.com \
    --provider aliyun \
    --cert-dir ./my-certs
```

### Route 3: Server-Client

Start an HTTP server to handle certificate requests and call it remotely via the client tool. Supports multi-tenant isolation (Token-based).

**Step 1: Start Server**
```bash
# Start on server, set auth token
chattool serve cert --token "my-secret-token" --provider aliyun
```

**Step 2: Client Call**
```bash
# Apply for certificate (Client side)
chattool client cert apply \
    -d example.com -d "*.example.com" \
    --token "my-secret-token" \
    --server http://<server-ip>:8000

# List certificates
chattool client cert list --token "my-secret-token" --server http://<server-ip>:8000

# Download certificate
chattool client cert download example.com --token "my-secret-token" --server http://<server-ip>:8000
```

### Route 4: MCP Protocol

Call tools via MCP protocol if the ChatTool MCP Server is running.

**Tool Name**: `dns_cert_update`

**Arguments**:
- `domains`: List[str] (e.g., `["example.com"]`)
- `email`: str
- `provider`: str ("aliyun" or "tencent")

**Example (JSON-RPC)**:
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
