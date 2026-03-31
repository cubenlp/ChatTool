# Workspace 协作脚手架（setup workspace）

`chattool setup workspace` 用来初始化一个围绕核心项目的“人类-AI 协作工作区”。

它不会把协议文件和知识沉淀塞进核心项目仓库里，而是在项目外围建立一层独立 workspace，用来承载：

- 人类当前意图与阶段目标
- 模型当前任务面
- 跨 session 记忆
- 任务产物
- 可复用知识、报告与工具笔记

## 1. 基本用法

```bash
chattool setup workspace
chattool setup workspace ~/workspace/demo
```

命令形态：

```bash
chattool setup workspace [PROFILE] [WORKSPACE_DIR] [--force] [--dry-run] [-i|-I]
```

- `PROFILE`：可选，当前仅支持 `base`
- `WORKSPACE_DIR`：可选，默认当前目录
- `--force`：覆盖已生成文件，但如果 `setup.md` 已包含 `completed:`，仍不会覆盖它
- `--dry-run`：只打印将创建的目录与文件，不写入磁盘
- `-i / -I`：强制交互 / 禁止交互

## 2. 生成结构

基础 workspace 结构如下：

```text
workspace/
├── AGENTS.md
├── MEMORY.md
├── setup.md
├── task.md
├── thoughts/
│   ├── README.md
│   └── current.md
├── tasks/
│   └── README.md
├── playground/
│   └── README.md
└── knowledge/
    ├── README.md
    ├── blog/
    ├── design/
    ├── memory/
    │   └── status/
    ├── report/
    │   └── README.md
    ├── skills/
    └── tools/
```

其中：

- `thoughts/current.md`：人类当前阶段关注点
- `task.md`：模型实时工作面
- `MEMORY.md`：跨 session 记忆
- `knowledge/report/`：主要的人类 review 界面

## 3. Profile

当前只保留 `base`，用于生成通用协作骨架。

## 4. dry-run

```bash
chattool setup workspace ~/workspace/demo --dry-run -I
```

适合先确认：

- 将创建哪些目录
- 将写哪些文件
- 生成骨架是否符合预期

## 5. force 与 setup.md 保护

```bash
chattool setup workspace ~/workspace/demo --force
```

`--force` 会覆盖多数生成文件，但有一个特例：

- 如果 `setup.md` 已包含 `completed:`，说明该 onboarding 已被后续模型消费并完成
- 这种情况下，即使传 `--force`，也不会覆盖 `setup.md`

这样可以避免把已经完成的项目适配清单误恢复成模板。
