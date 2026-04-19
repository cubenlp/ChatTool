# Projects

这里放当前所有实际进行中的工作。每个 project 都应该足够自洽，使执行阶段可以尽量只在该 project 内部完成。

当前版本面向 OpenCode `chatloop`：

- 前期对话先专注生成和完善 `PRD.md`
- 只有显式触发 `/chatloop ...` 后，loop 插件才会围绕 `PRD.md` 工作；模型每次停下后都会 fresh start，再从头阅读 `PRD.md`（以及必要的 `memory.md` / `progress.md`）

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

## 源码仓库访问

- 真实源码仓库默认保留在 `core/`
- 如果当前 project 需要更短的访问路径，可手动在 project 内创建符号链接，例如 `ln -s ../../core/ChatTool ./ChatTool`
- 该符号链接是按需行为，不作为默认模板自动生成

## 与 workspace-level `reference/` 的关系

- project 内的 `reference/` 只放本次任务局部参考、样例和阶段归档。
- 如果某类参考材料已经明显跨多个 project 可复用，应提升到 workspace 根目录 `reference/`。
- 如果某类参考材料长期依托某个源码仓库，可在 workspace-level `reference/` 中保存“任务起手参考”，再在具体 project 下按需链接 `core/<repo-name>`。

## 调试与停止

- `/chatloop-status` 可查看当前解析到的 project 根目录、状态文件和事件文件
- `chatloop` 的状态文件写入当前 project 根目录下的 `.opencode/chatloop.local.md`
- 事件记录直接追加到当前 project 根目录下的 `.opencode/chatloop.events.log`
- `chatloop` 首轮就会强制注入 `PRD.md` 路径、project path 和结构化进度规则
- 每轮应输出 `## Completed`、`## Next Steps` 和 `STATUS: IN_PROGRESS` / `STATUS: COMPLETE`
- 只有当完成标准已满足、`Next Steps` 没有未完成项，并且模型输出 `STATUS: COMPLETE` 与 `<complete>DONE</complete>` 时，插件才会停止 continuation

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
