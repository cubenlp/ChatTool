# test_chattool_gh_basic

测试 ChatTool 已移除内置 `gh` 入口，并且 alias 生成不再把 `chatgh` 映射到 `chattool gh`。

## 元信息

- 命令：`chattool gh`
- 目的：确认 GitHub 工作流迁移到独立 `chatgh` 后，ChatTool 不再暴露旧入口。
- 标签：`mock-cli`, `github`, `migration`
- 前置条件：`chatgh>=0.2.1` 作为独立 CLI 使用。

## 用例 1：不再注册 `chattool gh`

预期过程和结果：

1. 执行 `chattool --help`，命令列表中不包含 `gh`。
2. 执行 `chattool gh --help`，Click 返回 `No such command 'gh'`。

## 用例 2：不再生成 `chatgh` alias

预期过程和结果：

1. `ALIAS_MAP` 中不包含 `chatgh`。
2. 默认 alias block 中不包含 `chattool gh`。
