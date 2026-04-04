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

## 用例 4：为当前 GitHub 仓库配置 HTTPS token

- 初始环境准备：
  - 在临时目录初始化一个 git 仓库。
  - `origin` 指向一个 GitHub 仓库 URL。
  - mock 掉 `git config --global credential.helper store` 与 `git credential approve`。
- 相关文件：
  - 无。

预期过程和结果：
  1. 执行 `chattool gh set-token --token <pat>`。
  2. CLI 应从当前仓库 remote 自动解析出 `owner/name`。
  3. 应以带 path 的 GitHub HTTPS 凭据形式写入该仓库的 token，仅针对当前仓库。

参考执行脚本（伪代码）：

```sh
init temp git repo with github origin
run chattool gh set-token --token ghp_xxx
assert git credential approve receives protocol/host/path/username/password
```

## 用例 5：当前仓库不是 GitHub remote 时拒绝配置

- 初始环境准备：
  - 在临时目录初始化一个 git 仓库。
  - `origin` 指向非 GitHub URL。
- 相关文件：
  - 无。

预期过程和结果：
  1. 执行 `chattool gh set-token --token <pat>`。
  2. CLI 应报错说明当前仓库没有可识别的 GitHub remote。

参考执行脚本（伪代码）：

```sh
init temp git repo with non-github origin
run chattool gh set-token --token ghp_xxx
assert command fails with non-github remote message
```

## 用例 6：`origin` 不是 GitHub，但其它 remote 是 GitHub 时应自动回退

- 初始环境准备：
  - 在临时目录初始化一个 git 仓库。
  - `origin` 指向非 GitHub remote。
  - 另一个 remote（例如 `upstream`）指向 GitHub。
- 相关文件：
  - 无。

预期过程和结果：
  1. 执行 `chattool gh set-token --token <pat>`。
  2. CLI 应跳过非 GitHub 的 `origin`，并自动使用可识别的 GitHub remote。

参考执行脚本（伪代码）：

```sh
init temp git repo with gitlab origin and github upstream
run chattool gh set-token --token ghp_xxx
assert credential path uses upstream github repo
```

## 清理 / 回滚

- 无需额外操作。
