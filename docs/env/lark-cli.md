# Lark CLI 配置（setup 命令）

`chattool setup lark-cli` 用来安装官方 `lark-cli`，并把 ChatTool 当前保存的 Feishu 配置迁过去。

## 先看默认配置位置

官方 `lark-cli` 默认把配置写到：

```text
~/.lark-cli/config.json
```

如果设置了环境变量 `LARKSUITE_CLI_CONFIG_DIR`，则配置文件位置变为：

```text
$LARKSUITE_CLI_CONFIG_DIR/config.json
```

而 ChatTool 自己的 Feishu 默认配置位置是：

```text
~/.config/chattool/envs/Feishu/.env
```

如果设置了 `CHATTOOL_CONFIG_DIR`，则对应变为：

```text
$CHATTOOL_CONFIG_DIR/envs/Feishu/.env
```

这就是 `setup lark-cli` 的主要作用：直接把 ChatTool 这套现有配置复用给官方 CLI，避免再手工抄一次 `FEISHU_APP_ID` / `FEISHU_APP_SECRET`。

## 基本用法

直接复用当前保存的 Feishu 配置：

```bash
chattool setup lark-cli
```

显式指定某个 Feishu profile：

```bash
chattool setup lark-cli -e work
chattool setup lark-cli -e ~/.config/chattool/envs/Feishu/work.env
```

也可以完全手工传参：

```bash
chattool setup lark-cli \
  --app-id cli_xxx \
  --app-secret xxx \
  --brand feishu
```

## 参数优先级

`setup lark-cli` 的解析顺序是：

1. 显式参数：`--app-id`、`--app-secret`、`--brand`
2. `-e/--env` 指定的 Feishu 配置
3. 现有 `~/.lark-cli/config.json` 中已有的 app 元信息
4. shell 环境变量
5. 当前保存的 ChatTool Feishu `.env` 配置
6. 默认品牌值 `feishu`

其中 `-e/--env` 支持两种形式：

- `.env` 文件路径
- `Feishu` 类型下已保存的 profile 名称

## 实际执行了什么

命令内部会按这个顺序做事：

1. 检查 `Node.js >= 20` 和 `npm`
2. `npm install -g @larksuite/cli@latest`
3. 调用官方命令：

```bash
lark-cli config init --app-id <APP_ID> --app-secret-stdin --brand <feishu|lark>
```

这里特意使用 `--app-secret-stdin`，避免把 secret 暴露在进程参数列表里。

## 品牌值如何判断

- 默认 `FEISHU_API_BASE=https://open.feishu.cn` 时，品牌写成 `feishu`
- 如果当前 API base 指向 `https://open.larksuite.com`，则品牌会自动推断为 `lark`
- 也可以显式传 `--brand lark`

## 完成后的下一步

`setup lark-cli` 只负责安装和 app 配置初始化，不会自动替你做浏览器授权。

配置完成后继续执行：

```bash
lark-cli auth login --recommend
```

如果你还要给 Agent 安装官方技能，再执行：

```bash
npx skills add larksuite/cli -y -g
```
