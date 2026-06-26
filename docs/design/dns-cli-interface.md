# DNS CLI Interface Design

Date: 2026-05-07
Status: historical pre-extraction design for `rex/chatdns`

!!! note "Current ownership after ChatDNS extraction"
    This page records the pre-extraction nested `chattool dns` interface design. ChatTool no longer exposes `chattool dns` and no longer owns DNS/cert business logic. Current DNS, DDNS, IP, and DNS-01 certificate automation lives in the standalone `ChatDNS` package and first-level `chatdns` CLI, including `chatdns cert apply/check`. DNS MCP remains a separate follow-up boundary.

## Goal

Document the historical design that made `chattool dns` map cleanly to DNS provider capabilities while keeping task-oriented commands easy to discover.

## Command Tree

```text
chattool dns
  list      list domains in the provider account
  records   show DNS records for a domain or host record
  set       create or update one DNS record idempotently
  delete    delete DNS records after showing matches
  ddns      update one DNS record with the current IP
  ip        print the current public or local IP
  cert      manage Let's Encrypt certificates
    apply
    check
```

`get` is removed. Record lookup is named `records` so `list` consistently means domain list.

## `dns list`

Lists domains in the selected provider account.

```bash
chattool dns list
chattool dns list -p tencent --page 1 --page-size 50
```

Provider mapping:

```python
client.describe_domains(page_number=page, page_size=page_size)
```

Output fields should be human readable and stable enough for CLI inspection:

```text
DNS域名 (tencent):
DomainName                     DomainId           Status     Records  Remark
------------------------------------------------------------------------------------------
example.com                    12345              ENABLE     8        -
```

## `dns records`

Shows DNS records. The optional target can be a root domain or a full host name.

```bash
chattool dns records example.com
chattool dns records test.example.com
chattool dns records -d example.com -r test
chattool dns records example.com -t A
chattool dns records -d example.com -r @
```

Resolution rules:

```text
records example.com        -> domain=example.com, rr=None, list all records
records test.example.com   -> domain=example.com, rr=test
records -d example.com     -> domain=example.com, rr=None, list all records
records -d example.com -r @ -> domain=example.com, rr=@, show apex records
```

Provider mapping:

```python
client.describe_domain_records(domain, subdomain=rr, record_type=type)
```

## `dns set`

Creates or updates one record idempotently.

```bash
chattool dns set test.example.com -t A -v 1.2.3.4
chattool dns set -d example.com -r test -t A -v 1.2.3.4
chattool dns set -d example.com -r @ -t TXT -v hello
```

Provider mapping should prefer the common idempotent helper instead of deleting first:

```python
client.set_record_value(domain, rr, type, value, ttl)
```

This avoids deleting unrelated multi-value records as a side effect of a normal set operation.

## `dns delete`

Deletes records only after querying and showing the exact matches.

```bash
chattool dns delete test.example.com -t A
chattool dns delete test.example.com -t A -v 1.2.3.4
chattool dns delete -d example.com -r test -t A -v 1.2.3.4
chattool dns delete test.example.com -t A --yes
```

Rules:

- `--type/-t` is required to avoid broad accidental deletion.
- `--value/-v` is optional and narrows the match.
- Interactive terminals show matched records and ask for confirmation.
- Non-interactive deletion requires `--yes`; otherwise the command fails with guidance.

Provider mapping:

```python
records = client.describe_domain_records(domain, subdomain=rr, record_type=type)
for record in matched_records:
    client.delete_domain_record(record_id, domain_name=domain)
```

## `dns ddns`

Keeps the task-oriented command for writing the current IP to one record.

```bash
chattool dns ddns home.example.com
chattool dns ddns -d example.com -r home
chattool dns ddns nas.example.com --ip-type local
chattool dns ddns home.example.com --monitor
```

Provider/tool mapping:

```python
DynamicIPUpdater.run_once()
DynamicIPUpdater.run_continuous(interval)
```

## `dns ip`

Prints the current detected IP without touching DNS provider credentials or records.

```bash
chattool dns ip
chattool dns ip --type public
chattool dns ip --type local
chattool dns ip --type local --local-ip-cidr 192.168.1.0/24
```

This command reuses the same public/local IP detection semantics as DDNS but does not instantiate a DNS provider client.

## `dns cert`

Certificate management stays under a dedicated command group.

```bash
chattool dns cert apply -d example.com
chattool dns cert apply -d example.com -e admin@example.com --force
chattool dns cert check -d example.com
```

Old `chattool dns cert-update` is not exposed.

## Provider Capability Mapping

| Provider / helper capability | CLI |
| --- | --- |
| `describe_domains()` | `chattool dns list` |
| `describe_domain_records()` | `chattool dns records` |
| `describe_subdomain_records()` | `chattool dns records TARGET` / `-d -r` |
| `add_domain_record()` / `update_domain_record()` | `chattool dns set` via `set_record_value()` |
| `delete_domain_record()` / `delete_record_value()` | `chattool dns delete` |
| `DynamicIPUpdater.run_once()` | `chattool dns ddns` |
| public/local IP detection | `chattool dns ip` |
| `SSLCertUpdater.run_once()` | `chattool dns cert apply` |
