# test_chattool_gh_basic

测试 `chattool gh` 的新命令树 mock 基础链路，覆盖 `gh pr ...` / `gh run ...` 帮助信息、缺参自动补问、`--wait` / `--check` 参数透传，以及 `set-token` / `repo-perms` 的保留行为。

## 元信息

- 命令：`chattool gh <group> <command> [args]`
- 目的：验证新的嵌套入口 `pr` / `run` 可用，同时保留 ChatTool 的交互补问与 token 配置行为。
- 标签：`cli`、`mock`
- 前置条件：无真实 GitHub token 或远端仓库依赖；通过 monkeypatch 替换命令实现层。
- 环境准备：使用 `CliRunner` 调用统一入口 `chattool`。
- 回滚：只读 mock 测试，无需回滚。

## 用例 1：帮助信息可达

预期过程和结果：
1. 执行 `chattool gh --help`，输出包含 `pr`、`run`、`repo-perms`、`set-token`。
2. 执行 `chattool gh pr --help`，输出包含 `create`、`list`、`view`、`checks`、`comment`、`merge`、`edit`。

参考执行脚本（伪代码）：

```sh
chattool gh --help
chattool gh pr --help
```

## 用例 2：高频命令缺参时自动补问

预期过程和结果：
1. 执行 `chattool gh pr view`，自动补问 PR number。
2. 执行 `chattool gh pr create`，自动补问 `base` / `head` / `title`。
3. 执行 `chattool gh pr comment`，自动补问 PR number 和 comment body。
4. 执行 `chattool gh pr merge`，自动补问 PR number。
5. 执行 `chattool gh run view` / `chattool gh run logs`，分别自动补问 run id / job id。
6. 对同类命令传 `-I` 时，直接报缺参错误，不进入交互。

## 用例 3：`--wait` 和 `--check` 走新入口

预期过程和结果：
1. 执行 `chattool gh pr checks --number 138 --wait --interval 10 --timeout 600`。
2. CLI 应把 `wait=True`、`interval=10`、`timeout=600` 传给命令实现层。
3. 执行 `chattool gh pr merge --number 138 --check`。
4. CLI 应把 `check=True` 传给命令实现层。

## 用例 4：repo-perms 继续可用

预期过程和结果：
1. 执行 `chattool gh repo-perms --repo owner/repo`，输出仓库权限与 capability 摘要。
2. 执行 `chattool gh repo-perms --repo owner/repo --json-output --full-json`，输出 JSON 且带原始仓库 payload。

## 用例 5：set-token 保留当前仓库 token 配置行为

预期过程和结果：
1. 执行 `chattool gh set-token --token <pat>`，CLI 从当前 git remote 推断 GitHub 仓库并写入 repo-scoped HTTPS credential。
2. 传 `--save-env` 时，同时更新 ChatTool GitHub env。
3. 当前 remote 不是 GitHub 时，命令应拒绝执行。
4. `origin` 不是 GitHub 但其他 remote 是 GitHub 时，应自动回退到可识别的 GitHub remote。
5. TTY 下未传 token 时，可交互输入 token。
6. remote URL 无 `.git` 后缀时，应保留原 path，不强行追加 `.git`。

## 用例 6：repo-scoped exact token 规则未回归

预期过程和结果：
1. 当命令要求 `exact_only=True` 时，如果 credential store 里只有其它 GitHub repo 的 token，不应误用它。

## 清理 / 回滚

- 无需额外操作。
