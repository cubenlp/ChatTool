# test_chattool_gh_actions_diagnostics

测试 `chattool gh` 的 Actions 诊断 mock 链路，覆盖 workflow run 查看与 job 日志拉取。

## 元信息

- 命令：`chattool gh <command> [args]`
- 目的：验证 GitHub Actions 排错相关 CLI 的格式化输出与日志裁剪逻辑可用。
- 标签：`cli`、`mock`
- 前置条件：无真实 GitHub token 或 Actions run 依赖；通过 fake API 返回固定 run / job / logs 数据。
- 环境准备：使用 `CliRunner` 调用统一入口 `chattool`，并 monkeypatch GitHub API 访问函数。
- 回滚：只读操作，无需回滚。

## 用例 1：查看 workflow run 与 jobs

- 初始环境准备：
  - 准备有效 workflow run id。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool gh run-view --run-id <id>`，预期输出 workflow run 的状态、事件、分支、head sha 与 jobs 列表。
  2. 输出中的每个 job 应展示状态、结论、job id 和 GitHub 页面链接。
  3. 如果 job 附带 step 信息，输出中应展示 step 级别状态，方便定位失败点。
  4. 执行 `chattool gh run-view --run-id <id> --json-output`，预期返回机器可读 JSON。

参考执行脚本（伪代码）：

```sh
chattool gh run-view --run-id 23494900414
chattool gh run-view --run-id 23494900414 --json-output
```

## 用例 2：查看 job 日志

- 初始环境准备：
  - 准备有效 workflow job id。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool gh job-logs --job-id <id>`，预期输出该 job 的日志内容。
  2. 默认输出应控制在日志尾部，便于终端直接查看失败摘要。
  3. 执行 `chattool gh job-logs --job-id <id> --tail 0`，预期输出完整日志。
  4. 执行 `chattool gh job-logs --job-id <id> --output /tmp/job.log`，预期写入日志文件并在终端输出保存位置。
  5. 执行 `chattool gh job-logs --job-id <id> --json-output`，预期返回 job 元信息与日志文本。

参考执行脚本（伪代码）：

```sh
chattool gh job-logs --job-id 68373094563
chattool gh job-logs --job-id 68373094563 --tail 0
chattool gh job-logs --job-id 68373094563 --output /tmp/job.log
chattool gh job-logs --job-id 68373094563 --json-output
```
