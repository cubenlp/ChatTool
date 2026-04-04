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
Human
  -> thoughts/current.md · MEMORY.md
       -> reports/
       -> playgrounds/
       -> knowledge/

Workspace
  -> Core project | Reference material
```

这个 workspace 是包裹核心项目的一层协作脚手架。协作痕迹尽量都留在外层 workspace，核心项目保持干净。

## 关键文件职责

- `thoughts/current.md`：人的当前规划面。开工前先读，理解目标、约束和问题。
- `MEMORY.md`：跨 session 记忆。每次进入工作前都先读。
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

1. 先读 `thoughts/current.md`，理解当前阶段意图。
2. 开始任务时，先在 `playgrounds/<task-name>/` 下建立任务隔离工作区。
3. 对人同步进展时，在 `reports/<task-name>/` 下更新任务定义、阶段进展或最终总结。
4. 把可复用结论写入 `knowledge/`，让知识沉淀留在项目外层。
5. 结束前更新 `MEMORY.md`，保留下一次继续工作的必要上下文。

## 知识写入规则

| 情况 | 写入位置 |
|-----------|----------|
| 草稿 / 实验 / 临时工作文档 | `playgrounds/<task-name>/` |
| 给人的任务汇报 | `reports/<task-name>/` |
| 阶段总结 / 探索记录 | `knowledge/blog/YYYY-MM-DD-topic.md` |
| 架构决策 | `knowledge/design/NNN-title.md` |
| 状态快照 | `knowledge/memory/status/YYYY-MM-DD-status.md` |
| 工具使用发现 | `knowledge/tools/<toolname>/` |
| 可复用技巧 | `knowledge/skills/` |
| 暂时不确定 | 先写到 `knowledge/blog/`，之后再整理 |

## 约定

- `reports/` 只承载面向人的目标、阶段进展和最终总结。
- `playgrounds/` 也按任务文件夹整理，避免多任务互相污染。
- 不要超出当前任务边界。
- 不确定时要显式暴露，不要默默假设。
- 让核心项目保持干净，协议和知识沉淀留在这个 scaffold 中。
