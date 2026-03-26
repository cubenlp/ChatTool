# test_chattool_gh_basic

测试 `chattool gh` 的基础链路，覆盖 PR 列表、查看、检查与创建的命令流程。

## 元信息

- 命令：`chattool gh <command> [args]`
- 目的：验证 GitHub CLI 的基础功能可用。
- 标签：`cli`
- 前置条件：具备 GitHub token 与可访问仓库。
- 环境准备：配置 `GITHUB_ACCESS_TOKEN` 与 `GITHUB_DEFAULT_REPO`。
- 回滚：删除测试创建的 PR 与评论。

## 用例 1：列出 PR

- 初始环境准备：
  - 仓库可访问。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool gh pr-list --limit 5`，预期输出 PR 列表。

参考执行脚本（伪代码）：

```sh
chattool gh pr-list --limit 5
```

## 用例 2：查看 PR

- 初始环境准备：
  - 准备有效 PR 编号。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool gh pr-view --number <id>`，预期输出 PR 详情。

参考执行脚本（伪代码）：

```sh
chattool gh pr-view --number 1
```

## 用例 3：创建 PR

- 初始环境准备：
  - 准备 base/head 分支。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool gh pr-create --base main --head feature --title "test"`，预期返回 PR URL。

参考执行脚本（伪代码）：

```sh
chattool gh pr-create --base main --head feature --title "test" --body "demo"
```

## 用例 4：检查 PR 的 CI 状态

- 初始环境准备：
  - 准备有效 PR 编号，且该 PR 已触发 checks/workflows。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool gh pr-check --number <id>`，预期输出 PR 的 combined status、check runs 和 workflow runs。
  2. 执行 `chattool gh pr-check --number <id> --json-output`，预期返回机器可读 JSON。
  3. 执行 `chattool gh pr-check --number <id> --wait`，预期在 checks / workflow runs 未完成时持续轮询，直到全部结束后再输出最终结果；默认不设超时。
  4. 执行 `chattool gh pr-check --number <id> --wait --timeout <seconds>`，预期在超时后报错退出。

参考执行脚本（伪代码）：

```sh
chattool gh pr-check --number 1
chattool gh pr-check --number 1 --json-output
chattool gh pr-check --number 1 --wait
chattool gh pr-check --number 1 --wait --timeout 600
```

## 用例 5：评论与合并

- 初始环境准备：
  - 准备有效 PR 编号。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool gh pr-comment --number <id> --body "hello"`，预期返回评论链接。
  2. 如果希望在合并前做一次显式 CI 校验，执行 `chattool gh pr-merge --number <id> --method merge --confirm --check`。
  3. 若该 PR 仍有失败或未完成 checks / workflow runs，或当前相对 base 不可合并（如 `mergeable=False`、`mergeable_state=dirty`），CLI 应拒绝合并并提示先执行 `pr-check`。
  4. 不带 `--check` 时保持当前直连 GitHub merge 的行为，由调用者自行承担风险。

参考执行脚本（伪代码）：

```sh
chattool gh pr-comment --number 1 --body "hello"
chattool gh pr-merge --number 1 --method merge --confirm --check
chattool gh pr-merge --number 1 --method merge --confirm
```

## 用例 6：更新 PR

- 初始环境准备：
  - 准备有效 PR 编号。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool gh pr-update --number <id> --title "new"`，预期返回更新后的 PR URL。

参考执行脚本（伪代码）：

```sh
chattool gh pr-update --number 1 --title "new"
```

## 清理 / 回滚

- 删除测试 PR 与评论。
