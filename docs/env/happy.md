# Happy 配置（setup 命令）

`chattool setup happy` 用来安装 Happy CLI，并把一套围绕以下要素的 happy-coder bootstrap 收口起来：

- Happy 官方 server / webapp，或你自己的自建部署
- OpenAI-compatible relay（通过 `base_url` 接到 Codex / OpenCode）
- ChatTool 现有的 `workspace` / `playground` 协作脚手架

## 1. 基本用法

```bash
chattool setup happy
```

该命令会：

1. 检查 `Node.js >= 20` 与 `npm`
2. 安装 `happy` CLI（如果尚未安装）
3. 收集或复用 Happy / OpenAI-compatible relay 所需的配置
4. 输出一组推荐的后续命令

## 2. 写入 dedicated happy profile

如果你希望把 Happy 相关配置保存为可复用 profile：

```bash
chattool setup happy --write-env
```

会写入：

- `envs/Happy/happy.env`
- `envs/OpenAI/happy.env`

## 3. 官方模式与自建模式

### 官方模式

保留默认：

- `HAPPY_SERVER_URL=https://api.cluster-fluster.com`
- `HAPPY_WEBAPP_URL=https://app.happy.engineering`

然后执行：

```bash
happy auth login
```

### 自建模式

如果你自己部署了 Happy server / webapp，可以在 setup 时显式传入：

```bash
chattool setup happy \
  --server-url https://happy.example/api \
  --webapp-url https://happy.example/app \
  --base-url https://relay.example/v1 \
  --api-key sk-xxx \
  --write-env
```

这里的 `base_url` 不是 Happy server 本身，而是你要给 Codex / OpenCode 之类 coding agent 使用的 OpenAI-compatible relay。

## 4. 推荐后续步骤

```bash
chatenv use happy -t openai
chattool setup codex -e happy
chattool setup opencode -e happy
chattool setup workspace ~/workspace/happy
happy auth login
```
