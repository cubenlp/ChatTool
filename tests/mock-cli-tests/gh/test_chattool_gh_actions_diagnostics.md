# test_chattool_gh_actions_diagnostics

测试 ChatTool 中旧的 `chattool gh run ...` Actions 诊断入口已迁移到独立 `chatgh`。

## 元信息

- 命令：`chattool gh run <command>`
- 目的：确认 ChatTool 不再承载 GitHub Actions 诊断 CLI。
- 标签：`mock-cli`, `github`, `migration`

## 用例：旧入口不可用

预期过程和结果：

1. 执行 `chattool gh run view --run-id <id>`。
2. Click 返回 `No such command 'gh'`。
3. 后续 GitHub Actions 诊断应使用 `chatgh run view` / `chatgh run logs`。
