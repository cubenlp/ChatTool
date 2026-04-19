# Workspace Agents

`AGENTS.md` 是模型进入这个 workspace 后的入口说明。

## 核心原则

- workspace 根目录文件用于辅助创建和约束 project；真正执行任务时，应进入对应 project 目录埋头推进。
- 所有实际工作统一放到 `projects/` 下。
- project 默认使用最小 `PRD.md` 工作流，不预先写死复杂目录层级。
- `PRD.md` 只记录稳定需求、范围、约束和完成标准；进展细节写入 `progress.md`。
- 需求不清晰时，先补问题，再执行。

具体的 project 目录结构与命名规则，统一看 `projects/README.md`。

## 架构

```text
Workspace/
  README.md
  MEMORY.md
  TODO.md
  projects/
  reference/
  docs/
  core/
  skills/
  public/
```

这个 workspace 是包裹源码仓库的一层协作脚手架，协作痕迹尽量留在外层。

## 当前配置项

- 已启用项：`{{ENABLED_OPTIONS}}`
- 需要修改的源码仓库放到 `core/`
- 长期文档放到 `docs/`
- 导入的共享 skills 放到 `skills/`
- 对外发布产物放到 `public/`
- 跨多个 project 可复用的长期参考放到 `reference/`
- 按主题整理的长期维护约定放到 `docs/themes/`

## 工作流

1. 开始前先读 `MEMORY.md`。
2. 识别当前要改的仓库到 `core/`，并进入目标 project。
3. 先补齐 `PRD.md`，再开始执行。
4. 草稿、实验和局部参考都放在当前 project 内部。
5. 如需从 project 根目录直接访问源码仓库，可按需手动创建到 `core/<repo-name>` 的符号链接，但不要复制仓库。
6. 收尾时完成汇报，并在需要时更新 `MEMORY.md`。
7. 如果某类材料已明显跨多个 project 可复用，优先提升到 workspace 根目录 `reference/` 或 `docs/themes/`，而不是继续堆在单个 project 中。

## 写入规则

| 情况 | 写入位置 |
|-----------|----------|
| 任意实际工作单元 | `projects/MM-DD-<project-name>/` |
| 跨 project 可复用参考 | `reference/` |
| 需要修改的源码仓库 | `core/<repo-name>/` |
| 状态快照 / 长期上下文 | `docs/memory/YYYY-MM-DD-status.md` |
| 工具使用发现 | `docs/tools/<toolname>.md` |
| 可复用技巧 / skill 说明 | `docs/skills/` |
| 主题化维护约定 | `docs/themes/` |

## 约定

- 不要超出当前任务边界；如需扩展，先说明或单独开任务。
- 不确定时要显式说明，不要默默假设。
- workspace 根目录的 `reference/` 用于沉淀跨多个 project 可复用的长期参考；不要把一次性草稿和局部样例直接堆进去。
- `docs/themes/` 用于沉淀按主题整理的长期规范，例如 changelog、project 清理、workspace 维护约定。
