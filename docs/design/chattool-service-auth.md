# ChatTool Service Auth Design

Date: 2026-05-07
Status: design draft

## Goal

Provide a simple reusable auth mechanism for `chattool serve ...` services and local `chattool client ...` callers.

The target model is:

```text
local CLI -> access token -> ChatTool service API -> scoped capability
```

The local machine should not need cloud provider root credentials. The service machine keeps those secrets and exposes only allowed actions.

## Tokens

### Access Token

Short-lived token used on every API request:

```http
Authorization: Bearer <access_token>
```

Recommended expiry: 15-60 minutes.

### Refresh Token

Long-lived token used by local CLI to get new access tokens.

Requirements:

- Can be revoked.
- Can be rotated.
- Can be bound to a client profile/device.
- Should be stored as a hash on the server.
- Should have a max lifetime, for example 30-180 days.

### Scopes

Scopes describe what a token may do:

```text
service:info
dns:read
dns:write
dns:delete
cert:read
cert:apply
artifact:download
```

Dangerous operations should have separate scopes. For DNS, `dns:delete` should not be implied by `dns:write` unless the server owner explicitly chooses that policy.

## Login / Connect Modes

### Pairing Code Mode

Best for personal servers and private infrastructure.

```bash
chattool serve dns --pairing-code
chattool client connect dns-prod https://dns.example.com --code 123456
```

Flow:

```text
1. Server generates a short-lived one-time pairing code.
2. Local client sends the code to `/auth/pair`.
3. Server returns access token, refresh token, expiry, and scopes.
4. Local client stores the profile.
5. Pairing code is invalidated.
```

This is the simplest first-phase flow.

### Username / Password Mode

Best for public or multi-user cloud services.

```bash
chattool client login dns-prod https://dns.example.com --username rex
```

Flow:

```text
1. Local client sends username/password to `/auth/login`.
2. Server validates credentials.
3. Server returns access token, refresh token, expiry, and scopes.
4. Local client stores the profile.
```

This requires password hashing, rate limiting, and audit logs. It can be added after pairing-code mode.

## Common Auth Endpoints

```text
POST /auth/pair
POST /auth/login
POST /auth/refresh
POST /auth/revoke
```

### Pair

```http
POST /auth/pair
Content-Type: application/json

{
  "code": "123456",
  "client_name": "maopc",
  "service": "dns"
}
```

Response:

```json
{
  "access_token": "...",
  "access_token_expires_in": 3600,
  "refresh_token": "...",
  "refresh_token_expires_in": 7776000,
  "token_type": "Bearer",
  "scopes": ["dns:read", "dns:write"]
}
```

### Refresh

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "..."
}
```

Response returns a fresh access token. Prefer refresh token rotation: return a new refresh token and revoke the old one.

### Revoke

```http
POST /auth/revoke
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "refresh_token": "..."
}
```

## Local Client Profile

A profile contains the remote connection state:

```json
{
  "name": "dns-prod",
  "service": "dns",
  "server_url": "https://dns.example.com",
  "refresh_token": "...",
  "access_token": "...",
  "access_token_expires_at": "2026-05-07T12:00:00Z",
  "scopes": ["dns:read", "dns:write"],
  "created_at": "2026-05-07T00:00:00Z"
}
```

Client behavior:

```text
1. Read profile.
2. If access token is valid, use it.
3. If access token is expired, refresh it.
4. If refresh fails, ask user to reconnect.
```

## Server-Side Checks

Every protected endpoint should check:

- access token validity;
- required scope;
- service-specific policy, such as allowed domains;
- operation-level constraints, such as no delete unless explicitly allowed.

Example DNS constraints:

```json
{
  "allowed_domains": ["example.com", "*.example.org"],
  "allowed_actions": ["domains:list", "records:list", "cert:apply"],
  "denied_actions": ["records:delete"]
}
```

## Audit Log

Minimum audit record:

```json
{
  "time": "2026-05-07T00:00:00Z",
  "request_id": "req_...",
  "client_id": "maopc",
  "profile": "dns-prod",
  "service": "dns",
  "action": "records:delete",
  "target": "test.example.com/A",
  "scopes": ["dns:delete"],
  "result": "success"
}
```

## First Phase Recommendation

Start with:

- opaque tokens, not JWT;
- pairing code connect;
- refresh token storage by hash;
- scoped token checks;
- per-service policy;
- local profile + auto refresh.

JWT and username/password login can come later if multi-instance or public SaaS needs appear.
