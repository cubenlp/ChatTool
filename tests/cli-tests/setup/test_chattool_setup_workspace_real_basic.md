# test_chattool_setup_workspace_real_basic

验证 `chattool setup workspace` 在真实 CLI 下的基础落盘、`projects/` 为核心的 workspace 模板、显式英文模板，以及新建工作区和已有工作区两条不同 onboarding 路径。

## 元信息

- 命令：`chattool setup workspace`
- 目的：验证 workspace 骨架目录、以 `projects/` 为核心的 project 模型、语言选项，以及根目录 `README.md` 的 general-use 入口作用。
- 标签：`cli`
- 前置条件：无
- 环境准备：使用临时目录作为 workspace 根目录，不污染仓库。
- 回滚：测试结束后临时目录自动删除。

## 用例 1：base workspace 落盘基础骨架

- 初始环境准备：
  - 创建空临时目录作为 workspace 根目录。

预期过程和结果：
  1. 执行 `chattool setup workspace <workspace-dir> -I`，预期命令成功。
  2. 预期生成 `AGENTS.md`、`MEMORY.md`、`README.md`、`projects/README.md`、`docs/README.md`。
  3. `AGENTS.md` 默认应包含中文的 `projects/` 模型，并说明单任务 project 与多任务 project 两种结构。
  4. `AGENTS.md` 还应明确：review 由 loop 在模型准备停下时触发；如果是开发任务，每个阶段要先测试通过、文档完善，再按 `review.md` 的规则完成校验与收尾。
  5. 根目录 `README.md` 应明确：workspace 根目录用于 general-use 协议与上下文，project 目录用于实际执行。

参考执行脚本（伪代码）：

```sh
chattool setup workspace /tmp/demo-workspace -I
assert workspace files exist
assert AGENTS.md contains projects model rules
assert README.md contains general-use workspace description
```

## 用例 2：显式 `--language en` 时写入英文模板

- 初始环境准备：
  - 创建空临时目录作为 workspace 根目录。

预期过程和结果：
  1. 执行 `chattool setup workspace <workspace-dir> --language en -I`。
  2. `AGENTS.md` 应包含 `## Architecture`，且不包含 `## 架构`。
  3. `README.md` 应使用英文 general-use 文案。

参考执行脚本（伪代码）：

```sh
chattool setup workspace /tmp/demo-workspace --language en -I
assert AGENTS.md contains English headings
assert README.md uses English general-use text
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

## 用例 4：已有 workspace 时保留现有协议，并通过根目录 README 提供当前入口

- 初始环境准备：
  - 创建一个已有 `AGENTS.md`、`MEMORY.md` 的 workspace 目录。

预期过程和结果：
  1. 执行 `chattool setup workspace <workspace-dir> -I`。
  2. 原有 `AGENTS.md`、`MEMORY.md` 保持不变。
  3. 不应生成 `AGENTS.generated.md`、`MEMORY.generated.md` 辅助文件。
  4. 根目录 `README.md` 应作为当前 workspace 的 general-use 入口存在。

参考执行脚本（伪代码）：

```sh
prepare existing AGENTS.md and MEMORY.md
chattool setup workspace /tmp/demo-workspace -I
assert existing protocol files unchanged
assert helper generated files do not exist
assert README.md exists
```
