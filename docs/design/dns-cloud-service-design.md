# DNS 云端服务设计

日期：2026-05-07
状态：设计草稿

## 目标

把 `chattool dns` 作为 ChatTool 服务化能力的第一个试点。

拥有 Aliyun / Tencent DNS 密钥的机器运行 `chattool serve dns`。其他机器通过本地 `chattool dns ...` 或 `chattool client dns ...` 调用该服务，从而不需要复制云厂商密钥。

## 目标场景

```text
凭证机器：
  - 保存 Aliyun / Tencent DNS 密钥
  - 运行 ChatTool DNS 服务
  - 限定允许的域名和动作
  - 记录审计日志

目标机器：
  - 不保存云 DNS 密钥
  - 只保存 ChatTool service token
  - 可以发现服务端开放的能力
  - 继续使用熟悉的 CLI 命令
```

这个模式主要解决跨设备使用 DNS / 证书能力的问题：服务端集中保存高权限凭证，客户端只拿到受限、可撤销、可过期的访问能力。

## 预期用户流程

### 服务端机器

```bash
chattool serve dns \
  --provider aliyun \
  --allow-domain example.com \
  --allow-action domains:list \
  --allow-action records:list \
  --allow-action cert:apply \
  --pairing-code
```

这会启动一个只暴露选定 DNS / 证书能力的服务，并输出一次性配对码。

### 目标机器

```bash
chattool client connect dns-prod https://dns.example.com --code 123456
chattool client capabilities dns-prod
```

之后可以使用显式 client 命令：

```bash
chattool client dns list --profile dns-prod
chattool client dns records example.com --profile dns-prod
chattool client cert download example.com -o ./certs --profile dns-prod
```

也可以在后端抽象稳定后，让原始 CLI 路由到远程服务：

```bash
CHATTOOL_API_BASE=https://dns.example.com chattool dns list
CHATTOOL_API_BASE=https://dns.example.com chattool dns records example.com
```

长期 profile 用法可以更短：

```bash
chattool client use dns-prod
chattool dns list --remote
```

## 能力边界

第一阶段先做只读和证书相关能力，谨慎开放记录修改。

### 第一阶段候选能力

| 能力 | 本地 CLI | 服务 API | Scope |
| --- | --- | --- | --- |
| 服务信息 | `chattool client capabilities` | `GET /info` | `service:info` |
| 域名列表 | `chattool dns list` | `GET /dns/domains` | `dns:read` |
| 记录列表 | `chattool dns records` | `GET /dns/domains/{domain}/records` | `dns:read` |
| 申请证书 | `chattool dns cert apply` | `POST /cert/apply` | `cert:apply` |
| 检查证书 | `chattool dns cert check` | `GET /cert/domains/{domain}` | `cert:read` |
| 下载证书 | `chattool client cert download` | `GET /artifacts/certs/{domain}/{file}` | `artifact:download` |

### 后续能力

| 能力 | 本地 CLI | Scope |
| --- | --- | --- |
| 设置记录 | `chattool dns set` | `dns:write` |
| 删除记录 | `chattool dns delete` | `dns:delete` |
| DDNS 更新 | `chattool dns ddns` | `dns:write` |

记录修改类能力需要更强的 preview、dry-run、confirm 和审计，不建议第一阶段默认开放。

## 域名和动作策略

服务端必须同时限制域名和动作。

示例策略：

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

规则：

- 每个请求执行前都解析目标域名；
- 域名不在 policy 内时直接拒绝，即使 token scope 很宽；
- 危险动作必须同时满足 scope 和 policy allow；
- 本地 CLI 的 preview 只是用户体验，服务端仍必须强制校验；
- certificate artifact 的下载路径不能允许任意文件读取，只能下载服务端登记的产物。

## 服务发现

`GET /info` 返回目标机器当前可用的能力：

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

本地命令：

```bash
chattool client capabilities dns-prod
```

示例输出：

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

## API 草图

### 只读接口

```text
GET /dns/domains
GET /dns/domains/{domain}/records?rr=www&type=A
```

### 修改接口

```text
PUT    /dns/domains/{domain}/records/{rr}
DELETE /dns/domains/{domain}/records/{rr}?type=A&value=1.2.3.4
```

修改接口应优先支持 preview / dry-run，再执行：

```text
POST /dns/preview/delete
POST /dns/execute/delete
```

这和本地 CLI 的安全体验保持一致。

### 证书接口

```text
POST /cert/apply
GET  /cert/domains/{domain}
GET  /artifacts/certs/{domain}/{filename}
```

证书申请可能是异步任务：

```json
{
  "task_id": "task_...",
  "status": "pending"
}
```

随后查询任务：

```text
GET /tasks/{task_id}
```

## 本地 CLI 路由

有两种实现选择。

### 方案 A：显式 client 命令组

```bash
chattool client dns list --profile dns-prod
```

优点：

- 用户明确知道动作在远程执行；
- 不会和本地 provider 凭证混淆；
- 第一阶段实现成本更低。

### 方案 B：原始 CLI 支持远程后端

```bash
CHATTOOL_API_BASE=https://dns.example.com chattool dns list
chattool dns list --remote --profile dns-prod
```

优点：

- 复用原始 CLI 形态；
- 设置好 profile 后使用更自然；
- 符合“本地和远程接口一致”的长期目标。

建议：先实现方案 A，等 backend abstraction、错误模型和鉴权 profile 稳定后，再把方案 B 做成薄路由层。

## 和 MCP 的关系

DNS 服务 API 可以同时作为 CLI 和 MCP 的后端。

第一阶段推荐：

```text
MCP tool -> 本地 client profile -> DNS service API
```

这样登录、refresh、profile、capability discovery 都沉在同一层。MCP 只负责把 Agent 请求适配成 ChatTool client 调用，不单独维护鉴权系统。

## 第一阶段完成标准

设计层面先收敛到以下范围：

- DNS 服务端可声明 provider、allowed domains、allowed actions；
- client 可 connect、capabilities、调用只读 DNS 能力；
- 鉴权使用一次性配对码 + refresh token + 短期 access token；
- 证书能力先定义接口边界，实际实现可分后续 PR；
- 修改记录类能力默认不开放，只保留接口草图和安全要求。
