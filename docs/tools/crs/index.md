# CRS 工具

`chattool crs` 用于查询 Claude Relay Service（CRS）的用量、自统计和只读管理信息。第一版只覆盖获取相关接口：除 `auth login` 用于取得管理员 session token、`--save` 写入本地 ChatTool typed env 外，不调用 CRS 的创建、编辑、删除、刷新、测试或 OAuth 绑定接口。

## 配置

新增 typed env 类型：`crs` / `claude-relay`。

```bash
chatenv init -t crs
chatenv cat -t crs
chatenv cat -t crs --no-mask
```

字段：

- `CRS_API_BASE`：CRS 根地址，例如 `https://crs.example.com`，不要带 `/openai/v1`。
- `CRS_API_KEY`：CRS 下游 API key，通常是 `cr_...`，用于 `/apiStats/api/user-stats` 和 `/apiStats/api/user-model-stats`。
- `CRS_USERNAME`：管理员用户名，用于 `/web/auth/login`。
- `CRS_PASSWORD`：管理员密码，敏感字段。
- `CRS_ACCESS_TOKEN`：管理员 session token，敏感字段，可由 `chattool crs auth login --save` 写入。

如果已经有 OpenAI typed env 指向 CRS OpenAI 兼容端点，也可以临时复用：

```bash
chattool crs stats --openai-env apple
```

该模式会从 `OPENAI_API_BASE` 推导 CRS 根地址，并把 `OPENAI_API_KEY` 当作 `CRS_API_KEY` 使用。

## API Key 自查询

```bash
chattool crs stats
chattool crs models --period daily
chattool crs models --period monthly
chattool crs models --period alltime
```

`stats` 只需要 `CRS_API_KEY`，用于查看：

- API key 名称、ID、启用状态和权限；
- 请求数、token、cost；
- daily/window limit 信息；
- 绑定账号详情；
- OpenAI/Codex dedicated account 的 primary/secondary 窗口使用率和 reset 剩余时间（如果 CRS 返回该字段）。

需要原始响应时加：

```bash
chattool crs stats --json-output
chattool crs models --period daily --json-output
```

## 管理员登录

```bash
chattool crs auth login --save
chattool crs auth whoami
```

`auth login` 调用 `POST /web/auth/login`，使用 `CRS_API_BASE`、`CRS_USERNAME` 和 `CRS_PASSWORD`。加 `--save` 后会把返回 token 写入 active CRS typed env 的 `CRS_ACCESS_TOKEN`。

也可以显式传参并禁用交互：

```bash
chattool crs auth login \
  --api-base https://crs.example.com \
  --username admin \
  --password 'secret' \
  --save \
  -I
```

默认输出不会打印 token；如需调试原始响应，使用 `--json-output`，注意其中可能包含 session token。

## 只读 Admin 查询

```bash
chattool crs admin dashboard
chattool crs admin api-keys --page 1 --limit 20
chattool crs admin accounts --type openai
chattool crs admin accounts --type claude
chattool crs admin accounts --type openai-responses
chattool crs admin accounts --type gemini
```

这些命令使用 `CRS_ACCESS_TOKEN`，只调用 GET/read-only 管理接口：

- `GET /admin/dashboard`
- `GET /admin/api-keys`
- `GET /admin/openai-accounts`
- `GET /admin/claude-accounts`
- `GET /admin/openai-responses-accounts`
- `GET /admin/gemini-accounts`

缺少 token 时先执行：

```bash
chattool crs auth login --save
```
