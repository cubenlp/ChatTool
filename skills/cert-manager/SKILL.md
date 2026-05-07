---
name: cert-manager
description: Manage SSL certificates through ChatTool DNS-01 helpers, using `chattool dns cert apply/check`, typed DNS provider envs, server/client routes, or MCP `dns_cert_apply`.
version: 0.2.0
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

Relevant providers are `aliyun` and `tencent`.

## Usage Routes

| Route | Scenario | Core Tool |
| :--- | :--- | :--- |
| Code import | Python integration | `chattool.tools.cert.cert_updater.SSLCertUpdater` |
| CLI | Local ops and shell automation | `chattool dns cert apply` / `chattool dns cert check` |
| Server-client | Remote certificate service | `chattool serve cert` and `chattool client cert` |
| MCP | Agent tool call | `dns_cert_apply` |

## CLI Apply

```bash
chattool dns cert apply   -d example.com   -d "*.example.com"   -e admin@example.com   -p aliyun   --cert-dir ./certs
```

Useful options:

- `-d, --domain`: certificate domain; repeat for multiple domains.
- `-e, --email`: Let's Encrypt account email.
- `-p, --provider`: `aliyun` or `tencent`.
- `--cert-dir`: certificate output root.
- `--staging`: use Let's Encrypt staging.
- `--force`: skip local expiration checks.
- `-i/-I`: force or disable interactive input.

## CLI Check

```bash
chattool dns cert check   -d example.com   --cert-dir ./certs
```

Use `check` to inspect local certificate files without touching DNS or ACME.

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

## MCP

Tool name: `dns_cert_apply`

Arguments include:

- `domains`: list of domains.
- `email`: Let's Encrypt account email.
- `provider`: `aliyun` or `tencent`.
- optional certificate directory and staging/force controls if exposed by the MCP server.
