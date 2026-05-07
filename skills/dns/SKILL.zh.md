---
name: dns
description: 使用当前 ChatTool DNS CLI 和 MCP 工具管理 DNS 记录、DDNS 与 DNS-01 证书，并通过 chatenv typed provider profile 配置凭证。
version: 0.2.0
---

# DNS 管理

当需要查看或修改 DNS 记录、运行 DDNS、通过 ChatTool 申请证书时使用这个 skill。

## 配置

使用 `chatenv` typed env profile 配置 provider 凭证：

```bash
chatenv init -t ali
chatenv init -t aliyun
chatenv init -t tencent
chatenv cat -t ali
```

## 当前 CLI 命令

```bash
chattool dns list
chattool dns records --domain example.com
chattool dns set --domain example.com --rr www --type A --value 1.2.3.4
chattool dns delete --domain example.com --rr www --type A --yes
chattool dns ip
chattool dns ddns
chattool dns cert apply -d example.com -e admin@example.com -p aliyun
chattool dns cert check -d example.com --cert-dir certs
```

能力：

- `list`：列出 provider 账号下的域名。
- `records`：查看 DNS 记录。
- `set`：幂等创建或更新记录。
- `delete`：展示匹配记录并确认后删除。
- `ip`：查看当前公网或本地 IP。
- `ddns`：执行一次或持续运行动态 DNS 更新。
- `cert apply`：申请或续期 DNS-01 证书。
- `cert check`：检查本地证书文件。

## MCP 工具

- `dns_list_domains`
- `dns_get_records`
- `dns_add_record`
- `dns_delete_record`
- `dns_ddns_update`
- `dns_cert_apply`

## 安全规则

- 写入前确认 domain、host record、type 和 value。
- 更新记录时优先用幂等 `set`，不要随意 delete/add。
- `delete` 必须先查看匹配记录；自动化场景才显式使用 `--yes`。
- 用户输入含糊时不要执行破坏性 DNS 变更。
