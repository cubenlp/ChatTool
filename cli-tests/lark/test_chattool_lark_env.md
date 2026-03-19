# test_chattool_lark_env

测试 `chattool lark -e/--env` 的配置加载能力，覆盖 env 文件路径和 profile 名称两种入口。

## 元信息

- 命令：`chattool lark <command> -e <env>`
- 目的：验证飞书 CLI 可以从指定配置文件读取鉴权，而不是仅依赖当前 shell 环境变量。
- 标签：`cli`
- 前置条件：准备一份包含 `FEISHU_APP_ID` / `FEISHU_APP_SECRET` 的 `.env` 文件，或一个已保存的 profile。
- 回滚：删除测试用临时配置文件。

## 用例 1：通过 env 文件路径读取凭证

- 初始环境准备：
  - 创建临时 `.env` 文件，写入 `FEISHU_APP_ID` 与 `FEISHU_APP_SECRET`。
- 相关文件：
  - `<tmp>/.env`

预期过程和结果：
  1. 执行 `chattool lark info -e <tmp>/.env`。
  2. CLI 应从该文件加载配置，并完成机器人信息查询。

参考执行脚本（伪代码）：

```sh
chattool lark info -e /tmp/chattool-lark.env
```

## 用例 2：通过 profile 名称读取凭证

- 初始环境准备：
  - 在 `~/.config/chattool/envs/` 下准备一个 profile，例如 `work.env`。
- 相关文件：
  - `~/.config/chattool/envs/work.env`

预期过程和结果：
  1. 执行 `chattool lark info -e work`。
  2. CLI 应解析 profile 名称并加载对应配置。

参考执行脚本（伪代码）：

```sh
chattool lark info -e work
```
