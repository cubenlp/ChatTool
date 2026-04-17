# Projects

这里放当前所有实际进行中的工作。每个 project 都应该足够自洽，使执行阶段可以尽量只在该 project 内部完成。

当前版本面向 OpenCode `chatloop`：

- 前期对话先专注生成 `PRD.md`
- loop 插件只围绕 `PRD.md` 工作；模型每次停下后都会 fresh start，再从头阅读 `PRD.md`（以及必要的 `memory.md` / `progress.md`）

## 什么时候新开一个 project

当一项工作有自己明确的目标、上下文和交付物时，就应该新开一个 project。例如：

- 一次调研
- 一次性开发任务
- 一个 bugfix 流
- 一个后续可能拆成多个任务的大目标

## 命名规则

每个 project 目录默认使用 `MM-DD-<project-name>`。

## 默认结构

默认先从最简单的结构开始：

```text
MM-DD-<project-name>/
  PRD.md
  memory.md
  progress.md
  playground/
  reference/
```

这适合调研、一次性开发、局部清理等边界清楚的工作。

## 文件职责

- `PRD.md`：任务含义、目标、范围、约束、完成标准
- `memory.md`：局部上下文、关键文件、工作记忆
- `progress.md`：当前进展、关键决定、下一步
- `playground/`：草稿、实验、中间产物
- `reference/`：当前 project 局部参考和样例

其中：

- `PRD.md` 是唯一主入口
- `memory.md` / `progress.md` 是辅助上下文
- `chatloop` 每次停下后都会从 `PRD.md` 重新开始理解任务，而不是简单 continue

## 子目录拆分

如果一个 project 后续自然长出子任务，不需要预先引入复杂的 project/task 双层管理模型。

可以直接在当前目录下继续分子目录，并在子目录里放新的 `PRD.md`：

```text
MM-DD-<project-name>/
  PRD.md
  memory.md
  progress.md
  subtask-a/
    PRD.md
    memory.md
    progress.md
```

也就是说，层级由 `PRD.md` 自己演化出来，而不是由模板预先强制一套复杂项目级别管理结构。
