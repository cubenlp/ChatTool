# test_chattool_gh_basic

测试 `chattool gh` 的 mock 基础链路，覆盖帮助信息、PR 检查与合并前校验流程。

## 元信息

- 命令：`chattool gh <command> [args]`
- 目的：验证 GitHub CLI 编排层在 fake client 下的状态输出与拒绝合并逻辑。
- 标签：`cli`、`mock`
- 前置条件：无真实 GitHub token 或远端仓库依赖；通过 fake GitHub client 返回固定 PR / CI 数据。
- 环境准备：使用 `CliRunner` 调用统一入口 `chattool`，并 monkeypatch `chattool.tools.github.cli` 中的客户端解析函数。
- 回滚：只读 mock 测试，无需回滚。

## 用例 1：帮助信息可达

- 初始环境准备：
  - 无。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool gh --help`，预期输出包含 `pr-check` 与 `pr-merge`。

参考执行脚本（伪代码）：

```sh
chattool gh --help
```

## 用例 2：检查 PR 的 CI 状态

- 初始环境准备：
  - fake GitHub client 返回固定的 PR、combined status、check runs 和 workflow runs。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool gh pr-check --number <id>`，预期输出 PR 的 combined status、check runs 和 workflow runs。

参考执行脚本（伪代码）：

```sh
chattool gh pr-check --number 1
```

## 用例 3：阻止失败状态下的合并

- 初始环境准备：
  - fake GitHub client 返回失败的 check runs 与 workflow runs。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool gh pr-merge --number <id> --method merge --confirm --check`。
  2. 若 fake CI 结果中存在失败项，CLI 应拒绝合并并提示先执行 `pr-check`。
  3. fake `merge()` 不应被调用。

参考执行脚本（伪代码）：

```sh
chattool gh pr-merge --number 1 --method merge --confirm --check
```

## 清理 / 回滚

- 无需额外操作。
