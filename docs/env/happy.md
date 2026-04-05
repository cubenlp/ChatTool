# Happy 配置（setup 命令）

`chattool setup happy` 用来安装 Happy CLI，并把 Happy 自己的配置项收口起来：

- Happy 官方 hosted server / webapp
- 或者你自己的自建 Happy server / webapp
- Happy 本地 home 目录

## 1. 基本用法

```bash
chattool setup happy
```

该命令会：

1. 检查 `Node.js >= 20` 与 `npm`
2. 安装 `happy` CLI（如果尚未安装）
3. 可选保存 Happy 的 `server/webapp/home` 配置
4. 输出一组推荐的后续命令

## 3. 官方模式与自建模式

### 官方模式

不传 `--server-url` / `--webapp-url`，直接使用 Happy 自己的官方默认值。然后执行：

```bash
happy auth login
```

### 自建模式

如果你自己部署了 Happy server / webapp，可以在 setup 时显式传入：

```bash
chattool setup happy \
  --server-url https://happy.example/api \
  --webapp-url https://happy.example/app \
  --home-dir ~/.happy-selfhosted
```

这会把 Happy 的配置写到 ChatTool 的 `Happy/.env`，供你后续查看和复用。

## 4. 推荐后续步骤

```bash
chatenv cat -t happy
happy auth login
happy claude
```
