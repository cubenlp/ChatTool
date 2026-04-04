# Workspace Agents

`AGENTS.md` 是模型进入这个 workspace 后的入口说明。

## 核心原则

- 模型的进展和结果，统一在 `reports/` 中汇报。
- 报告按任务文件夹整理，例如 `reports/<task-name>/`。
- 每个任务目录至少包含 `TASK.md`、`progress.md` 和 `SUMMARY.md`。
- 多个任务并行时，`reports/` 和 `playgrounds/` 都按任务隔离。
- 每个任务在自己的 `playgrounds/<task-name>/` 里工作。
- 与汇报无关的草稿、实验和中间材料，不要放进 `reports/`。

## 架构

```text
Agent
  -> AGENTS.md
  -> MEMORY.md
  -> playgrounds/
  -> reports/
  -> knowledge/

Workspace
  -> Project(s) | Reference material
```

这个 workspace 是和 Agent 协作时使用的外层工作区，尽量不要把协作痕迹混进核心项目本身。

## 关键文件职责

- `MEMORY.md`：跨 session 的稳定记忆。记录长期有效的 workspace 约定。
- `reports/`：面向人的汇报区。按任务文件夹组织，每个任务至少包含 `TASK.md`、`progress.md` 和 `SUMMARY.md`。
- `playgrounds/`：模型的工作区根目录。每个任务在 `playgrounds/<task-name>/` 下隔离工作。
- `knowledge/`：可复用知识沉淀区。放研究、设计、经验和说明。

## Reports 结构

```text
reports/<task-name>/
  TASK.md
  progress.md
  SUMMARY.md
```

- `TASK.md`：任务目标、范围、背景、当前判断。作用更接近任务定义页。
- `progress.md`：阶段进展和当前状态。
- `SUMMARY.md`：最终结果和结论。

## 工作流

1. 先看 `AGENTS.md` 和 `MEMORY.md`，理解当前工作区约定。
2. 开始任务时，在 `playgrounds/<task-name>/` 下工作，避免和其他任务互相干扰。
3. 任务过程中的草稿、实验和中间材料，放在对应任务的 `playgrounds/<task-name>/` 或 `knowledge/` 的合适位置。
4. 需要对人同步时，在 `reports/<task-name>/` 下更新目标、阶段进展或最终总结。
5. 如果形成新的长期约定，再更新 `MEMORY.md`。

## 写入规则

| 情况 | 写入位置 |
|-----------|----------|
| 草稿 / 实验 / 临时工作文档 | `playgrounds/<task-name>/` |
| 给人的任务汇报 | `reports/MM-DD-<task-name>/` |
| 探索记录 / 研究结论 | `knowledge/blog/YYYY-MM-DD-topic.md` |
| 架构决策 | `knowledge/design/NNN-title.md` |
| 状态快照 | `knowledge/memory/YYYY-MM-DD-status.md` |
| 可复用技能 | `knowledge/skills/` |
| 暂时不确定 | 先写到 `knowledge/blog/`，之后再整理 |

## 约定

- `reports/` 只承载面向人的目标、阶段进展和最终总结。
- 报告按任务文件夹整理，不按阶段号组织。
- `playgrounds/` 也按任务文件夹整理，避免多任务互相污染。
- 与汇报无关的工作性文档，不要放进 `reports/`。
- 不要超出当前任务边界。
- 不确定时要显式暴露，不要默默假设。
- `reports/MM-DD-<task-name>/` 默认至少包含 `TASK.md`、`progress.md` 和 `SUMMARY.md`。

