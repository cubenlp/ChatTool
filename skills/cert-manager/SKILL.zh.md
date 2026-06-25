---
name: cert-manager
description: 通过 ChatTool 证书 helper、typed DNS provider env 与 server/client 路线管理 SSL 证书。旧 `chattool dns cert` 与 `dns_cert_apply` 路线已随 ChatDNS 分离撤出，等待单独证书边界 review。
version: 0.3.0
---

# 证书管理 Skill

用于通过 DNS 验证申请或续期 Let's Encrypt 证书。

## 配置

申请证书前先配置 provider 凭证：

```bash
chatenv init -t ali
chatenv init -t aliyun
chatenv init -t tencent
chatenv cat -t ali
```

相关 provider 为 `aliyun` 与 `tencent`。DNS provider client 当前由独立 `ChatDNS` 包提供。

## 使用路线

| 路线 | 场景 | 核心工具 |
| :--- | :--- | :--- |
| 代码导入 | Python 集成 | `chattool.tools.cert.cert_updater.SSLCertUpdater` |
| Server-client | 远程证书服务 | `chattool serve cert` 与 `chattool client cert` |

DNS 分离后，旧 nested CLI 路线 `chattool dns cert apply/check` 与 MCP 路线 `dns_cert_apply` 不再作为当前入口记录。证书自动化需要作为独立包/CLI 边界单独 review 后，再恢复一等本地 CLI 或 MCP 工具。

## 代码导入

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
