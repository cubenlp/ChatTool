# Workspace Agents

`AGENTS.md` 是模型进入这个 workspace 后的入口说明。

## 核心原则

- 外层根目录只保留少量总控文件；真正执行任务时，应进入对应 project 目录埋头推进。
- 所有实际工作统一放到 `projects/` 下；过时项目归档到 `archive/YYYY-MM-DD/`。
- project 目录结构默认保持最小化，但命名规则允许更灵活的分组方式。
- `PRD.md` 只记录稳定需求、范围、约束和完成标准；进展细节写入 `progress.md`。
- `progress.md` 是任务连续性的主日志。每次完成实质动作后，都应及时更新。
- 归档不应仅靠纯脚本决定。脚本适合做候选收集和规则检查，最终归档索引应由模型审查候选内容后写入 `archive/index.md`。
- 需求不清晰时，先补问题，再执行。

具体的 project 目录结构与命名规则，统一看 `projects/README.md`。

## 架构

```text
Workspace/
  AGENTS.md
  TODO.md
  ARCHIVE.md
  .trash/
  projects/
  archive/
    index.md
    YYYY-MM-DD/
  core/
  scripts/
  skills/
  public/
```

这个 workspace 是包裹源码仓库的一层协作脚手架，协作痕迹尽量留在外层。

## 当前配置项

- 已启用项：`archive/`、`ARCHIVE.md`、`archive/index.md`
- 需要修改的源码仓库放到 `core/`
- 维护脚本统一放到 `scripts/`
- workspace 根目录维护一个 `.trash/`，需要删除或清理文件时，默认优先移动到 `.trash/`
- 导入的共享 skills 放到 `skills/`
- 对外发布产物放到 `public/`
- 归档项目放到 `archive/YYYY-MM-DD/`

## 工作流

1. 先读当前根目录 `AGENTS.md`，再进入目标 project。
2. 识别当前要改的仓库到 `core/`，并进入目标 project。
3. 先补齐 `PRD.md`，再开始执行。
4. 每次完成实质动作后，及时更新当前 project 的 `progress.md`。
5. 草稿、实验和局部参考都放在当前 project 内部，并优先进入匹配职责的子目录。
6. 项目调试临时文件不要写到 `/tmp`；默认写到当前 project 的 `playground/`。
7. project 根目录默认只保留 `PRD.md`、`progress.md`、`memory.md` 等控制文件；报告放 `reports/`，脚本放 `scripts/`。
8. 若使用 `projects/<topic>/<name>/` 主题分组结构，则 `projects/<topic>/` 根目录只作为索引层，默认只保留 `README.md`、`.trash/` 与子项目目录。
9. 新建执行任务默认使用 `MM-DD-...` 日期前缀；只有明确的长期稳定子项目才可不带日期前缀。
10. workspace 和 project 级别都应优先准备 `.trash/`；需要删除文件时，默认先移动到就近的 `.trash/`，而不是直接 `rm`。
11. 如需从 project 根目录直接访问源码仓库，可按需手动创建到 `core/<repo-name>` 的符号链接，但不要复制仓库。
12. 收尾时完成汇报；如有归档动作，同步更新 `archive/index.md`。
13. 归档流程采用“脚本收集候选 + 模型审查 + 更新 `archive/index.md`”的方式，具体流程见根 `ARCHIVE.md`。

## 写入规则

| 情况 | 写入位置 |
|-----------|----------|
| 任意实际工作单元 | `projects/<name>/` 或 `projects/<topic>/<name>/` |
| 短期 project | 推荐 `MM-DD-<project-name>` |
| 长期 project | 可直接使用稳定名称，不加日期前缀 |
| 已不活跃的旧 project | `archive/YYYY-MM-DD/<project-name>/` |
| 归档操作指南 | `ARCHIVE.md` |
| 归档内容索引 | `archive/index.md` |
| 需要修改的源码仓库 | `core/<repo-name>/` |
| workspace 维护脚本 | `scripts/<name>.py` |

## 约定

- 不要超出当前任务边界；如需扩展，先说明或单独开任务。
- 不确定时要显式说明，不要默默假设。
- 避免在 workspace 顶层新增零散脚本或临时文件；需要保留的脚本统一放入 `scripts/`。
