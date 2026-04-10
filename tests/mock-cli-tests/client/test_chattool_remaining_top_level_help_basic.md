# test_chattool_remaining_top_level_help_basic

校对其余一级入口的 `--help`，确保顶层描述和一级 short help 风格一致，不再出现明显的中英混搭。

## 元信息

- 命令：`chattool <command> --help`
- 目的：覆盖 `dns`、`lark`、`tplogin`、`cc` 等剩余一级入口的 help 一致性。
- 标签：`cli`、`mock`
- 前置条件：无外部服务依赖。
- 环境准备：使用 `CliRunner` 调用统一入口 `chattool`。
- 回滚：无。

## 用例 1：`dns --help`

预期过程和结果：
1. 执行 `chattool dns --help`。
2. 顶层描述应为英文，并覆盖动态 DNS 与记录管理语义。

## 用例 2：`lark --help`

预期过程和结果：
1. 执行 `chattool lark --help`。
2. 子命令 short help 应与顶层英文风格一致。

## 用例 3：`tplogin --help`

预期过程和结果：
1. 执行 `chattool tplogin --help`。
2. 顶层描述和子命令 short help 应为英文，并能表达 router / ufw 语义。

## 用例 4：`cc --help`

预期过程和结果：
1. 执行 `chattool cc --help`。
2. 顶层描述和子命令 short help 当前可保留中文，但必须结构完整、信息充足。

## 清理 / 回滚

- 无需额外操作。
