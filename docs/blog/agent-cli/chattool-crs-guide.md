# ChatTool CRS 用法：在终端里查看 CRS 用量、窗口和只读后台信息

`chattool crs` 是 ChatTool 为 Claude Relay Service 增加的 CLI 工具。

它的目标很明确：**查询 CRS 的用量、模型统计和只读管理信息**。第一版刻意不做账号/API Key 的创建、编辑、删除、刷新、OAuth 绑定等动作，避免把高风险管理操作放进通用 CLI。

如果你已经有一个 CRS 部署，并且平时通过 OpenAI/Codex/Claude 客户端使用它，那么 `chattool crs` 主要解决两个问题：

- 快速查看自己的 `cr_...` key 用了多少；
- 快速查看 Codex / OpenAI dedicated account 的 primary、secondary 窗口剩余时间。

---

## 安装后的命令组

```bash
chattool crs --help
```

当前命令分三类：

```text
chattool crs stats
chattool crs models
chattool crs auth ...
chattool crs admin ...
```

其中：

- `stats` / `models` 使用 CRS API Key；
- `auth` 用管理员账号登录和验证 token；
- `admin` 只做 GET/read-only 查询。

---

## 配置 CRS typed env

ChatTool 新增了 typed env 类型：`crs` / `claude-relay`。

```bash
chatenv init -t crs
chatenv cat -t crs
```

对应字段：

```text
CRS_API_BASE
CRS_API_KEY
CRS_USERNAME
CRS_PASSWORD
CRS_ACCESS_TOKEN
```

含义：

- `CRS_API_BASE`：CRS 根地址，例如 `https://crs.example.com`，不要带 `/openai/v1`；
- `CRS_API_KEY`：下游使用的 CRS key，通常是 `cr_...`；
- `CRS_USERNAME`：管理员用户名；
- `CRS_PASSWORD`：管理员密码；
- `CRS_ACCESS_TOKEN`：管理员 session token，由 `auth login --save` 写入。

敏感字段在 `chatenv cat` 和普通输出中会脱敏。只有显式 `--no-mask` 才会显示明文，日常不要把这类输出贴到日志或 PR 里。

---

## 最常用：查看当前 key 的用量

```bash
chattool crs stats
```

这个命令调用 CRS 的：

```text
POST /apiStats/api/user-stats
```

只需要 `CRS_API_KEY`，不需要管理员 token。

它会汇总展示：

- API Key 名称、ID、启用状态、权限；
- 总请求数；
- token 数；
- cost；
- daily/window limit；
- 绑定账号信息；
- 如果 CRS 返回 Codex usage，则展示 primary / secondary 窗口百分比和 reset 剩余时间。

典型输出形态类似：

```text
API Key: openai
  ID: ...
  Active: yes
  Permissions: openai
Usage:
  Requests: 1,933
  Tokens: 207,431,171
  Cost: $342.69
Limits:
  Daily cost: 56.5358555 / -
Account[openai]: ...
  Type: dedicated
  Primary: 100% used, reset in 1h 49m
  Secondary: 67% used, reset in 4d 19h 59m
```

这正是平时想看“5h 70%”“重置剩余 2 小时”这类信息时最直接的入口。

---

## 查看模型统计

```bash
chattool crs models --period daily
chattool crs models --period monthly
chattool crs models --period alltime
```

这个命令调用：

```text
POST /apiStats/api/user-model-stats
```

用于查看当前 key 在不同模型上的请求量、token 和成本。

示例输出：

```text
- gpt-5.5: requests=283, tokens=33,995,203, cost=-
- gpt-5.4: requests=14, tokens=425,340, cost=-
```

---

## 复用已有 OpenAI profile

很多时候你已经有一个 OpenAI typed env 指向 CRS，例如：

```text
OPENAI_API_BASE='https://crs.example.com/openai/v1'
OPENAI_API_KEY='<CRS_API_KEY>'
OPENAI_API_MODEL='gpt-5.5'
```

这种情况下不一定要马上复制一份 CRS 配置，可以直接：

```bash
chattool crs stats --openai-env apple
chattool crs models --openai-env apple --period daily
```

ChatTool 会：

1. 读取 OpenAI profile；
2. 从 `OPENAI_API_BASE` 去掉 `/openai/v1`，推导 `CRS_API_BASE`；
3. 把 `OPENAI_API_KEY` 当作 `CRS_API_KEY` 使用。

这适合只查自用 key 用量的场景。

如果要使用 admin 查询，还是建议配置正式 CRS env。

---

## 管理员登录和 token 保存

管理员登录：

```bash
chattool crs auth login --save
```

它调用：

```text
POST /web/auth/login
```

需要：

- `CRS_API_BASE`
- `CRS_USERNAME`
- `CRS_PASSWORD`

`--save` 会把返回的 session token 保存到本机 ChatTool env：

```text
CRS_ACCESS_TOKEN
```

默认输出不会打印 token。

验证当前 token：

```bash
chattool crs auth whoami
```

它调用：

```text
GET /web/auth/user
```

如果 token 过期，重新执行：

```bash
chattool crs auth login --save
```

---

## 只读 admin 查询

`admin` 子命令需要 `CRS_ACCESS_TOKEN`。

### Dashboard

```bash
chattool crs admin dashboard
```

调用：

```text
GET /admin/dashboard
```

用于查看后台概览，例如 API Key 数量、账户数量、系统状态、请求概况等。

### API Keys

```bash
chattool crs admin api-keys --page 1 --limit 20
chattool crs admin api-keys --search openai
```

调用：

```text
GET /admin/api-keys
```

这是只读列表，不提供创建、更新、删除能力。

### 上游账户列表

```bash
chattool crs admin accounts --type openai
chattool crs admin accounts --type claude
chattool crs admin accounts --type openai-responses
chattool crs admin accounts --type gemini
```

对应只读接口：

```text
GET /admin/openai-accounts
GET /admin/claude-accounts
GET /admin/openai-responses-accounts
GET /admin/gemini-accounts
```

输出会尽量提取账号名、ID、active、schedulable、rate limit 状态，以及 OpenAI/Codex usage 窗口信息。

---

## JSON 输出

如果需要看 CRS 原始返回，可以加：

```bash
chattool crs stats --json-output
chattool crs models --period daily --json-output
chattool crs admin dashboard --json-output
```

注意：

```bash
chattool crs auth login --json-output
```

可能包含 session token。调试可以用，但不要把输出保存到公开日志或提交到仓库。

---

## 快捷入口

ChatTool 不再维护 shell alias；如需快捷入口，可以在自己的 shell 配置中手动添加：

```bash
alias chatcrs='chattool crs'
```

之后可以直接：

```bash
chatcrs stats
chatcrs models --period daily
chatcrs admin dashboard
```

---

## 为什么首版只做只读

CRS 后台的写接口很多，包括账号创建、账号更新、API Key 管理、OAuth 授权、状态重置、刷新 token 等。

这些动作都可能改变线上服务状态，风险比“查看用量”高很多。`chattool crs` 第一版选择只做读取，是为了把最常见、最安全、最高频的需求先稳定下来：

- 看 API key 用量；
- 看模型统计；
- 看 Codex 窗口重置时间；
- 看 dashboard 和账户状态。

如果后续要加写操作，应该按单独 PRD 设计确认，例如明确权限、确认提示、dry-run、审计日志和测试环境。

---

## 推荐工作流

如果只是查自己的 key：

```bash
chattool crs stats --openai-env apple
chattool crs models --openai-env apple --period daily
```

如果要长期管理某个 CRS：

```bash
chatenv init -t crs
chattool crs auth login --save
chattool crs auth whoami
chattool crs stats
chattool crs admin dashboard
```

如果只想快速看 Codex reset：

```bash
chattool crs stats
```

这就是 `chattool crs` 第一版最核心的使用场景。
