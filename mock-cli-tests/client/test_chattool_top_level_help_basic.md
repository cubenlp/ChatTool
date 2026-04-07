# test_chattool_top_level_help_basic

校对几个一级入口的 `--help`，确保顶层文案、子命令 short help 和实际暴露能力一致。

## 元信息

- 命令：`chattool <command> --help`
- 目的：防止一级 help 漂移成“没有 short help / 文案超出实际能力 / 英文说明太弱”的状态。
- 标签：`cli`、`mock`
- 前置条件：无外部服务依赖。
- 环境准备：使用 `CliRunner` 调用统一入口 `chattool`。
- 回滚：无。

## 用例 1：`client --help` 应显示子命令说明

预期过程和结果：
1. 执行 `chattool client --help`。
2. 输出中应包含 `cert`、`svg2gif`，且两者都带 short help。

## 用例 2：`serve --help` 应显示子命令说明

预期过程和结果：
1. 执行 `chattool serve --help`。
2. 输出中应包含 `capture`、`cert`、`lark`、`svg2gif` 的 short help。

## 用例 3：`skill --help` 应显示子命令说明

预期过程和结果：
1. 执行 `chattool skill --help`。
2. 输出中应包含 `install`、`list` 的 short help。

## 用例 4：`explore --help` 文案应与当前能力一致

预期过程和结果：
1. 执行 `chattool explore --help`。
2. 顶层描述应只承诺当前已暴露的能力，不再声称同时支持 `github` / `wordpress`。

## 清理 / 回滚

- 无需额外操作。
