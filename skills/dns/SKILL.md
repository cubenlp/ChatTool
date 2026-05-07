---
name: dns
description: Manage DNS records, DDNS, and DNS-01 certificates with current ChatTool DNS CLI commands and MCP tools, using chatenv typed provider profiles.
version: 0.2.0
---

# DNS Manager

Use this skill to inspect or change DNS records, run DDNS updates, or apply certificates through ChatTool.

## Configuration

Configure provider credentials with `chatenv` typed env profiles:

```bash
chatenv init -t ali
chatenv init -t aliyun
chatenv init -t tencent
chatenv cat -t ali
```

## Current CLI Commands

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

Capabilities:

- `list`: list domains in the provider account.
- `records`: show DNS records.
- `set`: create or update a record idempotently.
- `delete`: delete matching records after review/confirmation.
- `ip`: show current public or local IP.
- `ddns`: run dynamic DNS updates once or continuously.
- `cert apply`: request or renew DNS-01 certificates.
- `cert check`: inspect local certificate files.

## MCP Tools

- `dns_list_domains`
- `dns_get_records`
- `dns_add_record`
- `dns_delete_record`
- `dns_ddns_update`
- `dns_cert_apply`

## Safety Rules

- Confirm domain, host record, type, and value before writes.
- Prefer idempotent `set` over manual delete/add when updating records.
- Use `delete` only after reviewing matched records; require explicit confirmation or `--yes` for automation.
- Do not run destructive DNS changes from ambiguous user input.
