# test_chattool_gh_actions_diagnostics

测试 `chattool gh run ...` 的 Actions 诊断 mock 链路，覆盖 workflow run 查看与 job 日志查看。

## 元信息

- 命令：`chattool gh run <command> [args]`
- 目的：验证新的 `run view` / `run logs` 入口可直接用于 GitHub Actions 排错。
- 标签：`cli`、`mock`
- 前置条件：无真实 GitHub token 或 Actions run 依赖；通过 monkeypatch 替换命令实现层。
- 环境准备：使用 `CliRunner` 调用统一入口 `chattool`。
- 回滚：只读操作，无需回滚。

## 用例 1：查看 workflow run 与 jobs

预期过程和结果：
1. 执行 `chattool gh run view --run-id <id>`，输出 workflow run 的状态、事件、分支、head sha 与 jobs 列表。
2. job 输出中展示 step 级别状态，方便定位失败点。

参考执行脚本（伪代码）：

```sh
chattool gh run view --run-id 23494900414
```

## 用例 2：查看 job 日志

预期过程和结果：
1. 执行 `chattool gh run logs --job-id <id> --tail 2`，输出该 job 的尾部日志与失败摘要。

参考执行脚本（伪代码）：

```sh
chattool gh run logs --job-id 68373094563 --tail 2
```
