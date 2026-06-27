# Workspace 协作脚手架（setup workspace）

`chatup workspace` 用来初始化一个围绕核心项目的人类-AI 协作工作区。

当前模板以 `projects/` 为执行中心，同时显式区分活跃工作、归档历史和 workspace 级脚本。生成结果默认对齐当前 Playground 工作区风格，不再默认生成根 `README.md`、`IDENTITY.md` 或 `MEMORY.md`。

## 1. 基本用法

```bash
chatup workspace
chatup workspace ~/workspace/demo
chatup workspace ~/workspace/demo --language en
```

命令形态：

```bash
chatup workspace [PROFILE] [WORKSPACE_DIR] [--language zh|en] [--with-chattool] [--chattool-source PATH_OR_URL] [--with-chatblog] [--chatblog-source PATH_OR_URL] [--with-memory] [--memory-source PATH_OR_URL] [--force] [--dry-run] [-i|-I]
```

## 2. 基础结构

```text
workspace/
├── AGENTS.md
├── TODO.md
├── ARCHIVE.md
├── .trash/
├── projects/
├── archive/
│   └── index.md
├── core/
├── scripts/
├── skills/
└── public/
```

其中：

- `AGENTS.md`：模型执行协议
- `TODO.md`：这个 workspace 近期打算做的事
- `ARCHIVE.md`：归档操作指南
- `.trash/`：workspace 级软删除缓冲区
- `projects/`：所有实际工作的执行容器
- `archive/`：归档后的历史 project；`archive/index.md` 记录已归档内容索引
- `scripts/`：workspace 级维护脚本

## 3. `projects/` 模型

默认 project 形状：

```text
<project-root>/
  PRD.md
  progress.md
  memory.md
  .trash/
  reports/
  scripts/
  playground/
  reference/
```

## 4. 归档模型

- 活跃或近期仍在推进的工作保留在 `projects/`
- 明显不再活跃的项目移动到 `archive/YYYY-MM-DD/`
- 归档索引写入 `archive/index.md`
- 归档过程采用“脚本收集候选 + 模型审查 + 更新 `archive/index.md`”的方式，具体流程见根 `ARCHIVE.md`

## 5. 可选模块

- `ChatTool`：仓库放到 `core/ChatTool/`；ChatTool 不再携带或同步仓库内 `skills/`
- `ChatBlog`：仓库放到 `core/ChatBlog/`，并把 `source/_posts` 链接到 `public/chatblog`
- `ChatMemory`：仓库放到 `core/ChatMemory/`，只把共享 skill groups `Skills/chatarch`、`Skills/common` 和 `Skills/agents` 链接到 workspace 根目录 `skills/`；同时创建本地非共享目录 `skills/local`。`local` 用于当前机器/当前 workspace 的特定内容，不从 ChatMemory link，也不公开共享
