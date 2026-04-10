# test_chattool_setup_workspace_real_basic

验证 `chattool setup workspace` 在真实 CLI 下的基础落盘、支持“默认常规任务 + 可选任务集”的并发 workspace 模板、显式英文模板，以及新建工作区和已有工作区两条不同 onboarding 路径。

## 元信息

- 命令：`chattool setup workspace`
- 目的：验证 workspace 骨架目录、默认常规任务与任务集并存的 `reports/` / `playgrounds/` 模板、语言选项，以及 `setup.md` 的新建/迁移双语义与保护行为。
- 标签：`cli`
- 前置条件：无
- 环境准备：使用临时目录作为 workspace 根目录，不污染仓库。
- 回滚：测试结束后临时目录自动删除。

## 用例 1：base workspace 落盘基础骨架

- 初始环境准备：
  - 创建空临时目录作为 workspace 根目录。

预期过程和结果：
  1. 执行 `chattool setup workspace <workspace-dir> -I`，预期命令成功。
  2. 预期生成 `AGENTS.md`、`MEMORY.md`、`setup.md`、`reports/README.md`、`playgrounds/README.md`、`docs/README.md`。
  3. `AGENTS.md` 默认应包含中文的多任务协作架构，并同时说明常规任务 `reports/MM-DD-<task-name>/` / `playgrounds/<task-name>/` 与任务集 `reports/MM-DD-<set-name>/` / `playgrounds/task-sets/<set-name>/` 规则。
  4. `AGENTS.md` 还应明确：任务未完成前不要阶段性邀请 review；如果是开发任务，每个阶段要先测试通过、文档完善并自行 review。
  5. `setup.md` 应包含 Discover / Ask / Adapt / Initialise / Create first task lane / Done 六步清单，并明确默认完整做完后再统一汇报结果。

参考执行脚本（伪代码）：

```sh
chattool setup workspace /tmp/demo-workspace -I
assert workspace files exist
assert AGENTS.md contains reports/playgrounds task isolation rules
assert setup.md contains six-step checklist
```

## 用例 2：显式 `--language en` 时写入英文模板

- 初始环境准备：
  - 创建空临时目录作为 workspace 根目录。

预期过程和结果：
  1. 执行 `chattool setup workspace <workspace-dir> --language en -I`。
  2. `AGENTS.md` 应包含 `## Architecture`，且不包含 `## 架构`。
  3. `setup.md` 应使用英文 checklist 标题。

参考执行脚本（伪代码）：

```sh
chattool setup workspace /tmp/demo-workspace --language en -I
assert AGENTS.md contains English headings
assert setup.md uses English checklist title
```

## 用例 3：`--dry-run` 只展示计划，不写文件

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

## 用例 4：已有 workspace 时生成迁移辅助文件，而不是直接覆盖协议

- 初始环境准备：
  - 创建一个已有 `AGENTS.md`、`MEMORY.md` 的 workspace 目录。

预期过程和结果：
  1. 执行 `chattool setup workspace <workspace-dir> -I`。
  2. 原有 `AGENTS.md`、`MEMORY.md` 保持不变。
  3. 新生成 `AGENTS.generated.md`、`MEMORY.generated.md` 作为迁移参考。
  4. `setup.md` 应切换为 migration guide，明确迁移完成后可删除辅助文件。

参考执行脚本（伪代码）：

```sh
prepare existing AGENTS.md and MEMORY.md
chattool setup workspace /tmp/demo-workspace -I
assert existing protocol files unchanged
assert helper generated files exist
assert setup.md contains migration checklist
```

## 用例 5：`setup.md` 已完成时，即使 `--force` 也不得覆盖

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
