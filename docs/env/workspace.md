# Workspace 协作脚手架（setup workspace）

`chattool setup workspace` 用来初始化一个围绕核心项目的“人类-AI 协作工作区”。

当前版本采用“基础 workspace + 可选配置项”的结构，但任务组织模型已经从旧的 `reports/` / `playgrounds/` 分桶切换到新的 `projects/` 模型。

新建工作区时，命令会直接生成可用的 `README.md`、`AGENTS.md`、`MEMORY.md`。如果目标目录已经像一个 workspace，命令不会贸然覆盖现有 `AGENTS.md` / `MEMORY.md`，而是保留现有协议，同时补齐当前 general-use 的 `README.md` 和结构目录。

基础目录固定生成：

- `projects/`
- `docs/`
- `core/`
- `skills/`
- `public/`

其中：

- `projects/`：所有实际进行中的 project 容器根目录；默认从最小 `PRD.md` project 开始
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
chattool setup workspace [PROFILE] [WORKSPACE_DIR] [--language zh|en] [--with-opencode-loop] [--force] [--dry-run] [-i|-I]
```

- `PROFILE`：可选，当前仅支持 `base`
- `WORKSPACE_DIR`：可选，默认当前目录
- `--language`：模板语言，默认 `zh`，也可显式传 `en`
- `--with-opencode-loop`：启用 OpenCode loop-aware 模板版本，并把全局 `chatloop` plugin / slash commands 安装到 OpenCode home
- `--force`：覆盖已生成文件
- `--dry-run`：只打印将创建的目录与文件，不写入磁盘
- `-i / -I`：强制交互 / 禁止交互

补充语义：

- 如果目标目录已存在 `AGENTS.md` / `MEMORY.md` 等 workspace 标记，优先保留现有协议文件，并补齐当前 general-use 的 `README.md` 与 `projects/` 结构，而不是直接改写现有协议。

## 2. 基础结构

```text
workspace/
├── README.md
├── AGENTS.md
├── MEMORY.md
├── TODO.md
├── projects/
├── docs/
├── core/
├── skills/
└── public/
```

## 3. `projects/` 模型

### 默认 project

```text
projects/MM-DD-<project-name>/
  PRD.md
  progress.md
  memory.md
  playground/
  reference/
```

如果后续工作自然长出子部分，可以继续在子目录里放新的 `PRD.md`，而不是预先引入复杂项目级别管理结构。

源码仓库访问约定：

- 真实源码仓库默认保留在 `core/`
- 如果当前 project 需要更短的访问路径，可手动在 project 内创建到 `core/<repo-name>` 的符号链接
- 该符号链接是按需行为，不作为模板默认自动生成

### 设计原则

- workspace 根目录文件用于 general-use 协议与跨 session 上下文
- 实际执行时，应该进入具体 `project` 目录埋头推进
- `PRD.md` 是唯一主入口，用于定义任务含义、需求、范围、约束和完成标准
- `memory.md` / `progress.md` 用于补充当前上下文与进展
- 只有显式触发 `/chatloop ...` 时，`chatloop` 才会在 idle 时 fresh start，重新读取 `PRD.md`（以及必要的 `memory.md` / `progress.md`）

## 4. 可选配置项

交互模式下可以追加额外模块。

### OpenCode loop-aware template

- 使用 `--with-opencode-loop` 时，会切换到 loop-aware workspace 模板版本
- 同时会自动执行一次 OpenCode CLI 的纯安装（等价于 `chattool setup opencode --install-only`）
- 同时把 `chatloop` 全局安装到 OpenCode home（默认 `~/.config/opencode/`，也可通过 `OPENCODE_HOME` 改写），包括：
  - `plugins/chatloop/`
  - `command/chatloop.md`
  - `command/chatloop-status.md`
  - `command/chatloop-help.md`
  - `command/chatloop-stop.md`
- 该版本适合把 `PRD.md` 作为唯一入口，并通过显式 `/chatloop ...` 触发 fresh-start continuation 的工作流
- `chatloop` 可从任意 project 子目录触发，会自动向上寻找最近的 `PRD.md`
- 运行后，状态文件写入当前 project 根目录 `.opencode/chatloop.local.md`，事件记录直接追加到 project 根目录 `chatloop.events.log`
- 可通过 `/chatloop-status` 查看当前解析到的 project 根目录、状态文件和事件文件
- 当完成标准已满足时，模型应输出 `<complete>DONE</complete>`，插件会据此停止 continuation

### ChatTool

- 仓库放到 `core/ChatTool/`
- 从仓库内 `skills/` 同步到 workspace 根目录 `./skills/`
- 交互模式下会直接进入该仓库的 GitHub token 输入；默认值优先从当前仓库对应的 `.git-credential` / `.git-credentials` 读取，并以 mask 形式展示，回车可直接复用

### RexBlog

- 仓库放到 `core/RexBlog/`
- 把 `source/_posts` 链接到 `./public/hexo_blog`
- `public/` 根目录默认附带 `README.md`，说明这里用于部署公开网站
- 交互模式下同样会直接进入 GitHub token 输入，可复用当前仓库 token；若暂时不填，也可稍后进入目标仓库执行 `chattool gh set-token`

## 5. 设计原则

- `workspace` 是基础模型
- 额外仓库和发布能力通过“可选配置项”叠加
- 不再为每个场景分叉新的 workspace 命令
- 默认完整做完后再统一汇报结果
- 如果是开发任务，每个阶段要先测试通过、完善文档，再按当前 project 的完成标准收尾

## 6. dry-run

```bash
chattool setup workspace ~/workspace/demo --dry-run -I
```

适合先确认：

- 将创建哪些目录
- 将写哪些文件
- 将启用哪些可选配置项

## 7. General-Use Entry

当前模型不再依赖 `setup.md` 作为主要入口文件。

工作区的一般入口改为：

- `README.md`：给人和模型的 general-use 说明
- `AGENTS.md`：模型执行协议
- `MEMORY.md`：跨 session 高优先级上下文

如果是已有 workspace，优先保留现有 `AGENTS.md` / `MEMORY.md`，再通过新的 `README.md` 和 `projects/` 结构逐步迁移。
