# ChatTool Service API Layers

Date: 2026-05-07
Status: design draft

## Goal

Define a general path for turning a ChatTool capability into multiple entry points without duplicating business logic:

1. pure code implementation that produces functions/classes;
2. local CLI wrapping the packaged functions;
3. service API wrapping the same packaged functions;
4. local CLI or MCP calling the service API as a remote backend.

The long-term goal is that local CLI and remote API keep the same semantics. A command that supports service execution should only add backend selection and connection options, not invent a second workflow.

## Why This Matters

Some ChatTool capabilities should stay local. Others are better served from a controlled machine:

- DNS and certificate operations need cloud credentials and domain-level policy.
- Browser/Selenium/GPU conversion tasks need heavy dependencies.
- Webhook and bot services need long-running processes.
- Agent/MCP clients may need a stable API backend instead of direct local secrets.

A service API can become the shared backend for both CLI and MCP while still preserving the simple local CLI experience.

## Layer Model

### Layer 1: Code Capability

The base layer is a Python function/class with no CLI or HTTP assumptions.

Examples:

- `chattool.tools.dns.create_dns_client()`
- `chattool.tools.cert.SSLCertUpdater`
- SVG-to-GIF conversion helpers

Rules:

- Keep credentials and policy inputs explicit.
- Return structured results or raise predictable exceptions.
- Avoid Click, FastAPI, Rich, or MCP imports in the core capability.

### Layer 2: Local CLI

CLI adapts user input to the code capability.

Examples:

```bash
chattool dns list
chattool dns records example.com
chattool dns cert apply -d example.com
```

Rules:

- CLI owns human interaction, preview, confirmation, and local filesystem paths.
- CLI should use the same command shape whether the backend is local or remote.
- For service-capable commands, local CLI can choose backend from flags or env/profile.

Possible backend selection:

```bash
chattool dns list                         # local by default
chattool dns list --api-base https://...   # remote service
CHATTOOL_API_BASE=https://... chattool dns list
```

### Layer 3: Service API

Service API wraps the same code capability and enforces server-side policy.

Examples:

```bash
chattool serve dns --provider aliyun --allow-domain example.com --allow cert:apply
chattool serve cert --host 0.0.0.0 --port 8000
chattool serve svg2gif --host 0.0.0.0 --port 8000
```

Rules:

- Service owns credentials, capability whitelist, scope checks, audit logs, and async task state.
- Service should not expose arbitrary shell or arbitrary Python execution.
- Service endpoints should return structured JSON and stable error codes.

### Layer 4: Remote Client CLI / MCP

Remote client reuses the same user-facing capability but sends the action to a service API.

Two shapes can coexist:

```bash
chattool client dns list --profile dns-prod
chattool dns list --api-base https://dns.example.com
```

The first is explicit. The second is convenient when the local command can route to a remote backend.

MCP should initially reuse local client profiles instead of implementing a separate auth/profile system:

```text
Agent -> MCP/Skill -> local ChatTool CLI/client -> remote ChatTool serve API
```

## CLI and Service Interface Consistency

For service-capable features, local and remote modes should share the same operation names:

| Capability | Local CLI | Service API | Remote CLI |
| --- | --- | --- | --- |
| List domains | `chattool dns list` | `GET /dns/domains` | `chattool client dns list` |
| List records | `chattool dns records example.com` | `GET /dns/domains/{domain}/records` | `chattool client dns records example.com` |
| Set record | `chattool dns set ...` | `PUT /dns/domains/{domain}/records/{rr}` | `chattool client dns set ...` |
| Delete record | `chattool dns delete ...` | `DELETE /dns/...` | `chattool client dns delete ...` |
| Apply cert | `chattool dns cert apply ...` | `POST /cert/apply` | `chattool client cert apply ...` |

The CLI remains the main user interface. The service API is an execution backend.

## Environment and Profile Selection

A remote backend can be selected by a small set of connection fields:

```text
CHATTOOL_API_BASE=https://chattool.example.com
CHATTOOL_API_TOKEN=...
CHATTOOL_API_PROFILE=dns-prod
```

Design preference:

- `CHATTOOL_API_BASE` can be a quick override.
- Named client profiles are better for persistent use.
- Existing service-specific variables can remain as compatibility aliases.

Example:

```bash
chattool client connect dns-prod https://dns.example.com --code 123456
chattool client use dns-prod
chattool dns list --remote
```

## Service Discovery

Every service should expose a small discovery endpoint:

```text
GET /health
GET /info
```

`/info` should include:

```json
{
  "service": "dns",
  "version": "0.1",
  "capabilities": ["domains:list", "records:list", "records:set"],
  "scopes": ["dns:read", "dns:write"],
  "limits": {
    "allowed_domains": ["example.com"]
  }
}
```

The local client can show this as:

```bash
chattool client capabilities dns-prod
```

## Relationship to MCP

MCP and service API are similar in that both expose capabilities to non-human callers. The difference is ownership:

- MCP is an Agent protocol adapter.
- Service API is an execution backend with credentials, policy, and audit.
- CLI is the stable human and script interface.

The service API can become a backend for both CLI and MCP. In the first phase, do not make MCP own connection/login. Let MCP reuse the same local client profile or call the same client abstraction.

## Phase 1 Abstraction Work

Before adding cloud services, define shared abstractions:

- Capability metadata: name, actions, input schema, output schema, scopes.
- Backend selection: local vs remote.
- Auth profile: server URL, token, scopes, expiry.
- Error model: structured error code/message/request id.
- Audit model: action, target, result, actor, request id.

This lets DNS become the pilot without hard-coding a one-off DNS cloud path.
