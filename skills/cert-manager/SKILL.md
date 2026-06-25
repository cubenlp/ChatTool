---
name: cert-manager
description: Manage SSL certificates through ChatTool certificate helpers, typed DNS provider envs, and server/client routes. The old `chattool dns cert` and `dns_cert_apply` routes were removed during ChatDNS extraction pending a separate certificate boundary review.
version: 0.3.0
---

# Cert Manager Skill

Use this skill for Let's Encrypt certificate requests or renewal through DNS validation.

## Configuration

Configure provider credentials with typed env profiles before applying certificates:

```bash
chatenv init -t ali
chatenv init -t aliyun
chatenv init -t tencent
chatenv cat -t ali
```

Relevant providers are `aliyun` and `tencent`. DNS provider clients are now supplied by the standalone `ChatDNS` package.

## Usage Routes

| Route | Scenario | Core Tool |
| :--- | :--- | :--- |
| Code import | Python integration | `chattool.tools.cert.cert_updater.SSLCertUpdater` |
| Server-client | Remote certificate service | `chattool serve cert` and `chattool client cert` |

The old nested CLI route `chattool dns cert apply/check` and MCP route `dns_cert_apply` are intentionally not documented as current entry points after DNS was extracted to `ChatDNS`. Certificate automation should be reviewed as its own package/CLI boundary before restoring a first-class local CLI or MCP tool.

## Code Import

```python
import asyncio
from chattool.tools.cert.cert_updater import SSLCertUpdater

async def main():
    updater = SSLCertUpdater(
        domains=["example.com", "*.example.com"],
        email="admin@example.com",
        dns_type="aliyun",
        cert_dir="./certs",
    )
    await updater.run_once()

asyncio.run(main())
```

## Server-Client

```bash
chattool serve cert --token "my-secret-token" --provider aliyun
chattool client cert apply -d example.com --token "my-secret-token" --server http://server:8000
chattool client cert list --token "my-secret-token" --server http://server:8000
chattool client cert download example.com --token "my-secret-token" --server http://server:8000
```
