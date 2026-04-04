# test_chattool_setup_lark_cli_env

测试 `chattool setup lark-cli -e ...` 对 Feishu 配置的读取顺序，聚焦配置解析层，不覆盖 npm 安装与 `lark-cli config init` 的外部执行链路。

## 元信息

- 命令：`chattool setup lark-cli -e <env>`
- 目的：验证 `setup lark-cli` 可显式复用 `Feishu` 配置，并遵守 `显式 env > 保存配置 > 环境变量` 的回退关系。
- 标签：`cli`
- 前置条件：无
- 环境准备：使用临时目录作为 `CHATTOOL_CONFIG_DIR`，在真实文件系统中构造 `envs/Feishu/`。
- 回滚：测试结束后临时目录自动删除。

## 用例 1：profile 优先于保存配置，保存配置优先于环境变量

- 初始环境准备：
  - 创建 `envs/Feishu/.env`
  - 创建 `envs/Feishu/work.env`
  - 设置进程环境变量 `FEISHU_*`

预期过程和结果：
  1. 显式读取 `work` profile 时，若 profile 中存在某个字段，预期它优先于保存的 active Feishu 配置。
  2. 若 profile 未提供某个字段，预期回退到 `envs/Feishu/.env`。
  3. 只有当保存配置也未提供某个字段时，才允许继续回退到进程环境变量。

## 用例 2：默认优先读取保存配置，再回退到环境变量

- 初始环境准备：
  - 创建 `envs/Feishu/.env`
  - 设置不同的进程环境变量 `FEISHU_*`

预期过程和结果：
  1. 默认读取 `setup lark-cli` 的基础 Feishu 配置时，预期优先采用保存的 `envs/Feishu/.env`。
  2. 若保存配置缺失某个字段，预期该字段才回退到进程环境变量。
