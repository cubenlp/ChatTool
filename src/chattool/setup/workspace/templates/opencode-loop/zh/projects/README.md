# Projects

这里放当前所有实际进行中的工作。每个 project 都应该足够自洽，使执行阶段可以尽量只在该 project 内部完成。

当前版本面向 OpenCode `chatloop`：

- 外层 project 文档负责把任务含义、需求和规范说清楚
- loop 插件只围绕 `PRD.md` 工作；模型每次停下后都会 fresh start，再从头阅读 `PRD.md`（以及必要的 `memory.md` / `progress.md`）

## 什么时候新开一个 project

当一项工作有自己明确的目标、上下文和交付物时，就应该新开一个 project。例如：

- 一次调研
- 一次性开发任务
- 一个 bugfix 流
- 一个后续可能拆成多个任务的大目标

## 命名规则

每个 project 目录默认使用 `MM-DD-<project-name>`。

## 单任务 project

默认先从最简单的结构开始：

```text
MM-DD-<task-name>/
  TASK.md
  progress.md
  review.md
  memory.md
  playground/
  reference/
```

这适合调研、一次性开发、局部清理等边界清楚的工作。

## 多任务 project

只有在工作确实需要多个协同任务时，才升级为多任务 project：

```text
MM-DD-<project-name>/
  PROJECT.md
  progress.md
  review.md
  tasks/
    <task-name>/
      TASK.md
      progress.md
      review.md
      memory.md
      playground/
      reference/
```

这适合存在顺序依赖、复杂依赖、或需要项目级调度和 review 的工作。

## 子任务命名

多任务 project 下的子任务目录不要求统一带日期。

可以按两种方式组织：

### 1. Ordered Tasks

如果任务之间存在明显前后顺序，可以直接在任务名里编码顺序：

```text
tasks/
  01-workspace-protocol/
  02-chatloop-plugin/
  03-install-chain/
```

这时项目级调度默认按序推进。

### 2. Review-Directed Tasks

如果依赖关系复杂，或者优先级需要动态判断，则任务名可以自由命名，由项目级 `review.md` 决定当前 active task：

```text
tasks/
  workspace-protocol/
  chatloop-plugin/
  install-chain/
```

默认优先使用更简单的方式：

- 有明确顺序时，用编号任务
- 没有明确顺序时，再由项目级 `review.md` 调度

## 文件职责

- `TASK.md`：任务目标、范围、验收
- `PROJECT.md`：项目目标、边界、阶段
- `progress.md`：当前进展、关键决定、下一步
- `review.md`：验证规则和通过后需要写入的结果产物
- `memory.md`：局部上下文、关键文件、工作记忆
- `playground/`：草稿、实验、中间产物
- `reference/`：当前 project 局部参考和样例

其中：

- `TASK.md` / `PROJECT.md` 负责写清任务或项目的含义、需求和边界
- `review.md` 负责写清停下时的验证规则，以及通过后要补写的结果产物
- `memory.md` / `progress.md` 负责平时执行阶段的上下文与进展

## 升级规则

默认先用单任务 project。只有当一个 task 已经不足以清楚描述和约束当前工作时，才引入 `tasks/` 结构。
