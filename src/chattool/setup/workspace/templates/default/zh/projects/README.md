# Projects

这里放当前所有实际进行中的工作。每个 project 都应该足够自洽，使执行阶段可以尽量只在该 project 内部完成。

## 什么时候新开一个 project

当一项工作有自己明确的目标、上下文和交付物时，就应该新开一个 project。例如：

- 一次调研
- 一次性开发任务
- 一个 bugfix 流
- 一个后续可能拆成多个任务的大目标

## 命名规则

每个 project 目录默认使用 `MM-DD-<project-name>`。

默认先从最简单的结构开始：

```text
MM-DD-<project-name>/
  PRD.md
  progress.md
  memory.md
  playground/
  reference/
```

这适合调研、一次性开发、局部清理等边界清楚的工作。

## 文件职责

- `PRD.md`：需求、范围、约束、预期交付和完成标准
- `progress.md`：当前进展、关键决定、下一步
- `memory.md`：局部上下文、关键文件、工作记忆
- `playground/`：草稿、实验、中间产物
- `reference/`：当前 project 局部参考和样例

其中：

- `PRD.md` 是主入口
- `progress.md` 只负责进展和关键决定
- `memory.md` 用于补充局部上下文

## 源码仓库访问

- 真实源码仓库默认保留在 `core/`
- 如果当前 project 需要更短的访问路径，可手动在 project 内创建符号链接，例如 `ln -s ../../core/ChatTool ./ChatTool`
- 该符号链接是按需行为，不作为默认模板自动生成

## 与 workspace-level `reference/` 的关系

- project 内的 `reference/` 只放本次任务局部参考、样例和阶段归档。
- 如果某类参考材料已经明显跨多个 project 可复用，应提升到 workspace 根目录 `reference/`。
- 如果某类参考材料长期依托某个源码仓库，可在 workspace-level `reference/` 中保存“任务起手参考”，再在具体 project 下按需链接 `core/<repo-name>`。

## 子目录演化

如果一个 project 后续自然长出子任务，不需要预先引入固定的项目管理层级。

可以直接在当前目录下继续分子目录，并在子目录里放新的 `PRD.md`：

```text
MM-DD-<project-name>/
  PRD.md
  progress.md
  memory.md
  subtask-a/
    PRD.md
    progress.md
    memory.md
```

目录层级应该跟着 `PRD.md` 演化，而不是先被模板写死。
