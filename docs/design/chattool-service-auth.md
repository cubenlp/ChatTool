# ChatTool 服务鉴权设计

日期：2026-05-07
状态：设计草稿

## 目标

为 `chattool serve ...` 和本地 `chattool client ...` 提供一套简单、可复用的鉴权机制。

第一阶段只考虑 refresh token 方案，不做账号密码登录。服务端通过一次性配对流程向本地 client 发放长期 refresh token；本地 client 再用 refresh token 向服务端换取短期 access token。

目标模型：

```text
本地 CLI -> access token -> ChatTool service API -> scope + 服务端策略 -> 受限能力
```

本地机器不需要持有云厂商根密钥。服务机器保存这些敏感凭证，并只暴露被允许的动作。

## 设计依据

参考 `docs/blog/agent-cli/oauth-refresh-token-guide.md` 的结论：

- refresh token 不是本地生成 access token 的算法种子；
- 客户端必须把 refresh token 交给授权服务器或服务端 token endpoint 校验；
- access token 是短期访问凭证，是否有效以资源服务器校验为准；
- refresh token 更适合做长期、可撤销、可轮换的连接凭证；
- refresh token rotation 场景下要避免并发刷新导致旧 token 重放。

ChatTool 这里不需要完整 OAuth SaaS 体系，但应复用这套核心思想：长期凭证只用于刷新，业务接口只接受短期 access token。

## Token 模型

### Access token

Access token 是每次调用服务 API 时携带的短期凭证：

```http
Authorization: Bearer <access_token>
```

建议：

- 有效期 15-60 分钟；
- 第一阶段使用 opaque token，由服务端查表或缓存校验；
- 绑定 client id、profile、scope、过期时间；
- 只用于访问业务接口，不用于换新长期凭证；
- 服务端可以随时撤销或让其自然过期。

### Refresh token

Refresh token 是本地 client 保存的长期连接凭证，只用于换取新的 access token：

```text
POST /auth/refresh
```

要求：

- 服务端只保存 hash，不保存明文；
- 可以被撤销；
- 可以轮换，成功刷新后返回新的 refresh token 并废弃旧 token；
- 绑定 client profile / 设备名 / service；
- 有最大生命周期，例如 30-180 天；
- 不允许拿 refresh token 直接访问 DNS、证书等业务接口。

### Scope

Scope 描述 token 可以做什么：

```text
service:info
dns:read
dns:write
dns:delete
cert:read
cert:apply
artifact:download
```

危险动作必须拆分 scope。比如 DNS 中 `dns:delete` 不应默认包含在 `dns:write` 里，除非服务端 owner 明确配置这种策略。

## 连接流程

### 一次性配对码

第一阶段推荐只实现配对码模式，适合个人服务器、家庭机房、公司内网和私有基础设施。

```bash
chattool serve dns --pairing-code
chattool client connect dns-prod https://dns.example.com --code 123456
```

流程：

```text
1. 服务端生成短期、一次性配对码，并在终端显示。
2. 本地 client 调用 /auth/pair，提交配对码、client_name 和期望 service。
3. 服务端校验配对码是否存在、未过期、未使用，并根据服务端策略决定 scope。
4. 服务端返回 access token、refresh token、过期时间和 scope。
5. 本地 client 保存 profile。
6. 服务端立即废弃该配对码。
```

配对码只负责“建立信任关系”。后续请求不再使用配对码，而是走 access token + refresh token。

## 鉴权接口

第一阶段接口保持最小：

```text
POST /auth/pair
POST /auth/refresh
POST /auth/revoke
```

暂不设计 `/auth/login`、账号密码、注册、找回密码等公共账户体系。

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

响应：

```json
{
  "access_token": "...",
  "access_token_expires_in": 3600,
  "refresh_token": "...",
  "refresh_token_expires_in": 7776000,
  "token_type": "Bearer",
  "client_id": "cli_...",
  "scopes": ["dns:read", "cert:apply"]
}
```

### Refresh

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "...",
  "client_id": "cli_..."
}
```

响应返回新的 access token。推荐 refresh token rotation：如果响应中包含新的 refresh token，客户端必须原子替换本地 profile 里的旧 token。

```json
{
  "access_token": "...",
  "access_token_expires_in": 3600,
  "refresh_token": "...",
  "refresh_token_expires_in": 7776000,
  "token_type": "Bearer",
  "scopes": ["dns:read", "cert:apply"]
}
```

并发刷新处理：

- 本地 client 对同一个 profile 加文件锁，避免多个进程同时 refresh；
- 服务端记录 refresh token 的 rotation 状态；
- 如果检测到已轮换 token 被重复使用，服务端可以撤销该 client 的 refresh token，并要求重新配对。

### Revoke

```http
POST /auth/revoke
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "client_id": "cli_...",
  "refresh_token": "..."
}
```

用途：

- 本地 `chattool client logout dns-prod` 主动断开；
- 服务端 owner 撤销某个 client；
- 发现 token 泄露后立即吊销长期凭证。

## 本地 client profile

本地 profile 保存远程连接状态：

```json
{
  "name": "dns-prod",
  "service": "dns",
  "server_url": "https://dns.example.com",
  "client_id": "cli_...",
  "refresh_token": "...",
  "access_token": "...",
  "access_token_expires_at": "2026-05-07T12:00:00Z",
  "scopes": ["dns:read", "cert:apply"],
  "created_at": "2026-05-07T00:00:00Z"
}
```

客户端行为：

```text
1. 读取 profile。
2. access token 未过期时直接使用。
3. access token 过期或即将过期时，用 refresh token 调 /auth/refresh。
4. refresh 成功后原子更新 profile。
5. refresh 失败时提示用户重新 connect。
```

存储建议：

- profile 文件权限限制为当前用户可读写；
- 默认不在普通 `cat` 输出里显示 token 明文；
- 后续可以接入系统 keyring，但第一阶段不强依赖。

## 服务端校验

每个受保护接口至少校验：

- access token 是否存在、未过期、未撤销；
- token 是否属于当前 service；
- token scope 是否覆盖当前动作；
- 服务端 policy 是否允许目标域名、目标路径或目标动作；
- 高风险动作是否需要额外 confirmation / dry-run 机制。

DNS 示例策略：

```json
{
  "allowed_domains": ["example.com", "*.example.org"],
  "allowed_actions": ["domains:list", "records:list", "cert:apply"],
  "denied_actions": ["records:delete"]
}
```

注意：scope 只代表“token 具备某类权限”，最终能否执行还必须过服务端 policy。比如 token 有 `cert:apply`，但请求域名不在 `allowed_domains` 内，服务端仍然必须拒绝。

## 审计日志

最小审计记录：

```json
{
  "time": "2026-05-07T00:00:00Z",
  "request_id": "req_...",
  "client_id": "cli_...",
  "profile": "dns-prod",
  "service": "dns",
  "action": "records:delete",
  "target": "test.example.com/A",
  "scopes": ["dns:delete"],
  "result": "denied"
}
```

审计日志优先记录高风险动作、失败鉴权、refresh 失败、token revoke 和 policy deny。

## 第一阶段建议

先做：

- opaque access token；
- 一次性配对码 connect；
- refresh token hash 存储；
- refresh token rotation；
- 本地 profile 自动刷新；
- scope + 服务端 policy 双重校验；
- revoke 和基础审计。

暂不做：

- 账号密码登录；
- 注册、找回密码、多租户账户体系；
- JWT 公钥发布和多实例鉴权；
- 浏览器 OAuth 授权页；
- 把第三方 Web access token 包装成 ChatTool API 凭证。

这样可以先满足“私有机器暴露受限能力”的核心需求，同时保留后续升级为更完整 OAuth/OIDC 的空间。
