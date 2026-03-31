# test_chattool_setup_workspace_real_basic

验证 `chattool setup workspace` 在真实 CLI 下的基础落盘、`--dry-run` 与 `setup.md` 保护语义。

## 元信息

- 命令：`chattool setup workspace`
- 目的：验证 workspace 骨架目录、关键模板文件，以及 `--force` / `--dry-run` 的真实行为。
- 标签：`cli`
- 前置条件：无
- 环境准备：使用临时目录作为 workspace 根目录，不污染仓库。
- 回滚：测试结束后临时目录自动删除。

## 用例 1：base workspace 落盘基础骨架

- 初始环境准备：
  - 创建空临时目录作为 workspace 根目录。

预期过程和结果：
  1. 执行 `chattool setup workspace <workspace-dir> -I`，预期命令成功。
  2. 预期生成 `AGENTS.md`、`MEMORY.md`、`setup.md`、`task.md`、`thoughts/current.md`、`tasks/README.md`、`playground/README.md`、`knowledge/README.md`。
  3. `AGENTS.md` 应包含 5 层协作架构和 knowledge 写入规则。
  4. `setup.md` 应包含 Discover / Ask / Adapt / Initialise / Set first task / Done 六步清单。

参考执行脚本（伪代码）：

```sh
chattool setup workspace /tmp/demo-workspace -I
assert workspace files exist
assert AGENTS.md contains architecture and write rules
assert setup.md contains six-step checklist
```

## 用例 2：`--dry-run` 只展示计划，不写文件

- 初始环境准备：
  - 创建空临时目录作为 workspace 根目录。

预期过程和结果：
  1. 执行 `chattool setup workspace <workspace-dir> --dry-run -I`。
  2. 预期输出将创建的目录和文件摘要。
  3. 预期 workspace 根目录不产生任何协议文件与知识目录。

参考执行脚本（伪代码）：

```sh
chattool setup workspace /tmp/demo-workspace --dry-run -I
assert output mentions dry run actions
assert workspace remains empty
```

## 用例 3：`setup.md` 已完成时，即使 `--force` 也不得覆盖

- 初始环境准备：
  - 先执行一次 `chattool setup workspace`。
  - 手工向 `setup.md` 末尾写入 `completed: YYYY-MM-DD`。

预期过程和结果：
  1. 再次执行 `chattool setup workspace <workspace-dir> --force -I`。
  2. 预期其余可覆盖文件按 force 规则更新。
  3. `setup.md` 保持原内容，不被覆盖。

参考执行脚本（伪代码）：

```sh
chattool setup workspace /tmp/demo-workspace -I
append completed marker to setup.md
chattool setup workspace /tmp/demo-workspace --force -I
assert setup.md still contains previous completed marker
```
