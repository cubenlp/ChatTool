# test_chattool_setup_lark_cli_env

测试 `chattool setup lark-cli -e ...` 对 Feishu 配置的读取顺序，聚焦配置解析层，不覆盖 npm 安装与 `lark-cli config init` 的外部执行链路。

## 元信息

- 命令：`chattool setup lark-cli -e <env>`
- 目的：验证 `setup lark-cli` 可显式复用 `Feishu` 配置，并遵守 `显式 env > 当前 feishu 配置 > 类型默认 .env` 的回退关系。
- 标签：`cli`
- 前置条件：无
- 环境准备：使用临时目录作为 `CHATTOOL_CONFIG_DIR`，在真实文件系统中构造 `envs/Feishu/`。
- 回滚：测试结束后临时目录自动删除。

## 用例 1：profile 优先于当前 feishu，当前 feishu 优先于类型默认 `.env`

- 初始环境准备：
  - 创建 `envs/Feishu/.env`
  - 创建 `envs/Feishu/work.env`
  - 设置进程环境变量 `FEISHU_*`

预期过程和结果：
  1. 显式读取 `work` profile 时，若 profile 中存在某个字段，预期它优先于当前 `feishu/lark` 生效配置。
  2. 若 profile 未提供某个字段，预期回退到当前 `feishu/lark` 生效配置。
  3. 若当前 `feishu/lark` 生效配置也未提供，预期再回退到 `envs/Feishu/.env`。
