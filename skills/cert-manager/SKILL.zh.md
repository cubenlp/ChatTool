---
name: cert-manager
description: 通过 ChatTool DNS-01 工具管理 SSL 证书，使用 `chattool dns cert apply/check`、typed DNS provider env、服务端/客户端路线或 MCP `dns_cert_apply`。
version: 0.2.0
---

# 证书管理 Skill

当需要通过 DNS 验证申请或续期 Let's Encrypt 证书时使用这个 skill。

## 配置

申请证书前先用 typed env 配置 DNS provider 凭证：

```bash
chatenv init -t ali
chatenv init -t aliyun
chatenv init -t tencent
chatenv cat -t ali
```

当前相关 provider 为 `aliyun` 和 `tencent`。

## 使用路线

| 路线 | 场景 | 核心工具 |
| :--- | :--- | :--- |
| 代码导入 | Python 集成 | `chattool.tools.cert.cert_updater.SSLCertUpdater` |
| CLI | 本机运维和 shell 自动化 | `chattool dns cert apply` / `chattool dns cert check` |
| Server-client | 远端证书服务 | `chattool serve cert` 与 `chattool client cert` |
| MCP | Agent 工具调用 | `dns_cert_apply` |

## CLI 申请

```bash
chattool dns cert apply -d example.com -d "*.example.com" -e admin@example.com -p aliyun --cert-dir ./certs
```

常用选项：

- `-d, --domain`：证书域名，可重复传入。
- `-e, --email`：Let's Encrypt 账户邮箱。
- `-p, --provider`：`aliyun` 或 `tencent`。
- `--cert-dir`：证书输出根目录。
- `--staging`：使用 Let's Encrypt 测试环境。
- `--force`：跳过本地过期检查。
- `-i/-I`：强制或禁止交互输入。

## CLI 检查

```bash
chattool dns cert check -d example.com --cert-dir ./certs
```

`check` 只检查本地证书文件，不触碰 DNS 或 ACME。

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

## MCP

工具名：`dns_cert_apply`

参数包括：

- `domains`：域名列表。
- `email`：Let's Encrypt 账户邮箱。
- `provider`：`aliyun` 或 `tencent`。
- 如 MCP server 暴露，也可传证书目录、staging、force 等控制项。
