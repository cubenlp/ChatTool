# DNS Cloud Service Design

Date: 2026-05-07
Status: design draft

## Goal

Use `chattool dns` as the first service-capable CLI family.

A machine with Aliyun/Tencent DNS credentials runs `chattool serve dns`. Other machines use local `chattool dns ...` or `chattool client dns ...` to call the service without receiving DNS provider credentials.

## Target Scenario

```text
Credential machine:
  - owns Aliyun/Tencent DNS keys
  - runs ChatTool DNS service
  - limits domains and actions
  - records audit logs

Target machine:
  - has no cloud DNS keys
  - connects with ChatTool service token
  - can discover allowed capabilities
  - runs familiar CLI commands
```

## Desired User Flow

### Server Machine

```bash
chattool serve dns \
  --provider aliyun \
  --allow-domain example.com \
  --allow-action domains:list \
  --allow-action records:list \
  --allow-action cert:apply \
  --pairing-code
```

This starts a service that exposes only selected DNS/cert capabilities.

### Target Machine

```bash
chattool client connect dns-prod https://dns.example.com --code 123456
chattool client capabilities dns-prod
```

Then either explicit client commands:

```bash
chattool client dns list --profile dns-prod
chattool client dns records example.com --profile dns-prod
chattool client cert download example.com -o ./certs --profile dns-prod
```

Or original CLI routed to remote backend:

```bash
CHATTOOL_API_BASE=https://dns.example.com chattool dns list
CHATTOOL_API_BASE=https://dns.example.com chattool dns records example.com
```

Longer term, a profile can make this shorter:

```bash
chattool client use dns-prod
chattool dns list --remote
```

## Capability Boundary

Start with read and cert operations before record mutation.

### Phase 1 Candidate Capabilities

| Capability | Local CLI | Service API | Scope |
| --- | --- | --- | --- |
| Service info | `chattool client capabilities` | `GET /info` | `service:info` |
| Domain list | `chattool dns list` | `GET /dns/domains` | `dns:read` |
| Record list | `chattool dns records` | `GET /dns/domains/{domain}/records` | `dns:read` |
| Cert apply | `chattool dns cert apply` | `POST /cert/apply` | `cert:apply` |
| Cert list/check | `chattool dns cert check` | `GET /cert/domains/{domain}` | `cert:read` |
| Cert download | `chattool client cert download` | `GET /artifacts/certs/{domain}/{file}` | `artifact:download` |

### Later Capabilities

| Capability | Local CLI | Scope |
| --- | --- | --- |
| Set record | `chattool dns set` | `dns:write` |
| Delete record | `chattool dns delete` | `dns:delete` |
| DDNS update | `chattool dns ddns` | `dns:write` |

## Domain and Action Policy

The server should enforce both domain and action limits.

Example policy:

```json
{
  "provider": "aliyun",
  "allowed_domains": ["example.com", "*.example.org"],
  "allowed_actions": [
    "domains:list",
    "records:list",
    "cert:apply",
    "cert:download"
  ],
  "denied_actions": ["records:delete"],
  "cert": {
    "allowed_domains": ["example.com", "*.example.com"],
    "output_dir": "/srv/chattool/certs"
  }
}
```

Rules:

- Every request resolves its target domain before execution.
- The server rejects domains outside policy even if token has broad scopes.
- Dangerous operations need both scope and policy allow.
- Local CLI preview is not enough; server must enforce policy.

## Discovery

`GET /info` returns what the target machine may do:

```json
{
  "service": "dns",
  "provider": "aliyun",
  "capabilities": [
    "domains:list",
    "records:list",
    "cert:apply",
    "cert:download"
  ],
  "scopes": ["dns:read", "cert:apply", "artifact:download"],
  "limits": {
    "allowed_domains": ["example.com", "*.example.com"],
    "mutations": false
  }
}
```

Local command:

```bash
chattool client capabilities dns-prod
```

Example output:

```text
Service: dns (aliyun)
Allowed domains:
- example.com
- *.example.com
Capabilities:
- domains:list
- records:list
- cert:apply
- cert:download
Mutations: disabled
```

## API Sketch

### Read APIs

```text
GET /dns/domains
GET /dns/domains/{domain}/records?rr=www&type=A
```

### Mutation APIs

```text
PUT    /dns/domains/{domain}/records/{rr}
DELETE /dns/domains/{domain}/records/{rr}?type=A&value=1.2.3.4
```

Mutations should return a preview or dry-run mode before execution:

```text
POST /dns/preview/delete
POST /dns/execute/delete
```

This mirrors local CLI safety for `dns delete`.

### Cert APIs

```text
POST /cert/apply
GET  /cert/domains/{domain}
GET  /artifacts/certs/{domain}/{filename}
```

Certificate application may be async:

```json
{
  "task_id": "task_...",
  "status": "pending"
}
```

Then:

```text
GET /tasks/{task_id}
```

## Local CLI Routing

There are two implementation options.

### Option A: Explicit Client Group

```bash
chattool client dns list --profile dns-prod
```

Pros:

- Clear that execution is remote.
- No ambiguity with local provider credentials.
- Easier to implement first.

### Option B: Original CLI with Remote Backend

```bash
CHATTOOL_API_BASE=https://dns.example.com chattool dns list
chattool dns list --remote --profile dns-prod
```

Pros:

- Reuses original CLI shape.
- Easier for users after setup.
- Aligns with the goal that local and remote interfaces are identical.

Recommendation: implement Option A first, then make Option B a thin router once the backend abstraction is stable.

## Relationship to MCP

The DNS service API can serve as a backend for CLI and MCP.

Preferred first phase:

```text
MCP tool -> local client profile -> DNS service API
```

This keeps login/profile/token refresh in one client layer. MCP should not grow a separate auth system.

## Open Questions

- Should cert download stay under `client cert`, or should `dns cert download` exist too?
- Should `CHATTOOL_API_BASE` be global, or service-specific like `CHATTOOL_DNS_API_BASE`?
- Should `dns list` default to remote if an active DNS client profile exists?
- How should domain wildcard policy be matched and displayed?
- Should mutation APIs require a two-step preview/execute protocol?
