# Workspace 协作脚手架（setup workspace）

`chattool setup workspace` 用来初始化一个围绕核心项目的“人类-AI 协作工作区”。

当前版本采用“基础 workspace + 可选配置项”的结构。

新建工作区时，命令会直接生成可用的 `AGENTS.md`、`MEMORY.md` 和 `setup.md`。如果目标目录已经像一个 workspace，命令不会贸然覆盖现有协议，而是额外生成 `AGENTS.generated.md`、`MEMORY.generated.md` 与迁移版 `setup.md`，作为迁移指南。

基础目录固定生成：

- `reports/`
- `playgrounds/`
- `docs/`
- `core/`
- `reference/`
- `skills/`
- `public/`

其中：

- `core/`：集中放需要加入 workspace 的源码仓库
- `skills/`：共享 skills 目录，默认放在 workspace 根目录
- `public/`：用于部署公开网站和相关发布内容

## 1. 基本用法

```bash
chattool setup workspace
chattool setup workspace ~/workspace/demo
chattool setup workspace ~/workspace/demo --language en
```

命令形态：

```bash
chattool setup workspace [PROFILE] [WORKSPACE_DIR] [--language zh|en] [--force] [--dry-run] [-i|-I]
```

- `PROFILE`：可选，当前仅支持 `base`
- `WORKSPACE_DIR`：可选，默认当前目录
- `--language`：模板语言，默认 `zh`，也可显式传 `en`
- `--force`：覆盖已生成文件
- `--dry-run`：只打印将创建的目录与文件，不写入磁盘
- `-i / -I`：强制交互 / 禁止交互

补充语义：

- 如果 `setup.md` 中已经标记 `completed: ...`，即使传 `--force` 也不会覆盖它。
- 如果目标目录已存在 `AGENTS.md` / `MEMORY.md` 等 workspace 标记，优先进入“迁移辅助”模式，而不是直接改写现有协议。

## 2. 基础结构

```text
workspace/
├── README.md
├── AGENTS.md
├── MEMORY.md
├── setup.md
├── TODO.md
├── reports/
├── playgrounds/
├── docs/
├── core/
├── reference/
├── skills/
└── public/
```

## 3. 可选配置项

交互模式下可以追加额外模块。

### ChatTool

- 仓库放到 `core/ChatTool/`
- 从仓库内 `skills/` 同步到 workspace 根目录 `./skills/`
- 交互模式下会直接进入该仓库的 GitHub token 输入；默认值优先从当前仓库对应的 `.git-credential` / `.git-credentials` 读取，并以 mask 形式展示，回车可直接复用

### RexBlog

- 仓库放到 `core/RexBlog/`
- 把 `source/_posts` 链接到 `./public/hexo_blog`
- `public/` 根目录默认附带 `README.md`，说明这里用于部署公开网站
- 交互模式下同样会直接进入 GitHub token 输入，可复用当前仓库 token；若暂时不填，也可稍后进入目标仓库执行 `chattool gh set-token`

## 4. 设计原则

- `workspace` 是基础模型
- 额外仓库和发布能力通过“可选配置项”叠加
- 不再为每个场景分叉新的 workspace 命令
- 默认完整做完后再统一汇报结果，不在任务未完成时阶段性邀请 review
- 如果是开发任务，每个阶段要先测试通过、完善文档并自行 review

## 5. dry-run

```bash
chattool setup workspace ~/workspace/demo --dry-run -I
```

适合先确认：

- 将创建哪些目录
- 将写哪些文件
- 将启用哪些可选配置项

## 6. setup.md 的两种模式

### 新建 workspace

- `setup.md` 会作为 onboarding checklist
- 引导模型先读 `AGENTS.md` / `MEMORY.md`
- 默认先创建常规 `task`，只有长期系列目标才切换到 `taskset`

### 已有 workspace

- `setup.md` 会作为 migration guide
- 会提示对照 `AGENTS.generated.md` / `MEMORY.generated.md` 迁移新版协议
- 迁移完成后可以删除这些辅助文件
