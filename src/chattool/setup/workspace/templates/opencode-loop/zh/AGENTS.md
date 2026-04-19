# Workspace Agents

`AGENTS.md` 是模型进入这个 workspace 后的入口说明。

## 核心原则

- workspace 根目录文件用于辅助创建和约束 project；真正执行任务时，应进入对应 project 目录埋头推进。
- 所有实际工作统一放到 `projects/` 下。
- 当前 workspace 已启用 OpenCode loop-aware 模式：外层协议负责帮助模型理解规范，内层 `chatloop` 只围绕 `PRD.md` 做 fresh-start continuation。
- 前期对话先专注生成和完善 `PRD.md`；执行阶段默认让模型围绕 `PRD.md` 推进。
- 如果有辅助上下文，可使用 `memory.md` 和 `progress.md`，但它们不是主入口。
- 如果当前 project 需要更短的源码路径，可在 project 内按需手动创建到 `core/<repo-name>` 的符号链接，但不作为默认自动行为。

具体的 project 目录结构与命名规则，统一看 `projects/README.md`。

## 架构

```text
Workspace/
  README.md
  MEMORY.md
  TODO.md
  projects/
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

## 工作流

1. 开始前先读 `MEMORY.md`。
2. 识别当前要改的仓库到 `core/`，并进入目标 project。
3. 先补齐 `PRD.md`，再开始 loop 或执行。
4. 草稿、实验和局部参考都放在当前 project 内部。
5. 只有显式触发 `/chatloop ...` 时，`chatloop` 才会在模型准备停下时 fresh start，让模型重新阅读 `PRD.md`，必要时再读 `memory.md` / `progress.md`。
6. 收尾时完成汇报，并在需要时更新 `MEMORY.md`。

## 写入规则

| 情况 | 写入位置 |
|-----------|----------|
| 任意实际工作单元 | `projects/MM-DD-<project-name>/` |
| 需要修改的源码仓库 | `core/<repo-name>/` |
| 状态快照 / 长期上下文 | `docs/memory/YYYY-MM-DD-status.md` |
| 工具使用发现 | `docs/tools/<toolname>.md` |
| 可复用技巧 / skill 说明 | `docs/skills/` |

## 约定

- 不要超出当前任务边界；如需扩展，先说明或单独开任务。
- 不确定时要显式说明，不要默默假设。
