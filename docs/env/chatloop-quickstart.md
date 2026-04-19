# ChatLoop Quickstart

这是一份从零开始的 `chatloop` 使用指南，演示如何围绕一个新项目建立 `PRD.md`，再通过 `/chatloop ...` 进入 PRD-driven 开发循环。

示例场景：为 `ChatTool` 设计并实现一个 `arxiv-explore` 工具。

## 1. 先安装 OpenCode 和 ChatLoop

确保本机已有 Node.js，然后安装 OpenCode CLI 与全局 `chatloop` 插件：

```bash
chattool setup nodejs
chattool setup opencode --install-only --plugin chatloop
```

安装完成后，`chatloop` 的 plugin 和 slash commands 会写到 OpenCode home。默认是：

```text
~/.config/opencode/
```

可以先在 OpenCode 里执行：

```text
/chatloop-help
/chatloop-status
```

如果当前目录还不是 project，`/chatloop-status` 会提示没有找到 `PRD.md`，这是正常的。

## 2. 创建 workspace

初始化一个带 OpenCode loop-aware 模板的 workspace：

```bash
chattool setup workspace ~/workspace/arxiv-demo --with-opencode-loop
```

生成后，核心目录大致如下：

```text
~/workspace/arxiv-demo/
  README.md
  AGENTS.md
  MEMORY.md
  projects/
  core/
  docs/
  skills/
  public/
```

如果你要改的源码仓库已经在别处，也可以手动放到 `core/`。

## 3. 创建一个 project

进入 `projects/`，新建本次工作的 project：

```bash
mkdir -p ~/workspace/arxiv-demo/projects/04-20-arxiv-explore-tool/{playground,reference}
```

然后至少准备这三个文件：

```text
projects/04-20-arxiv-explore-tool/
  PRD.md
  progress.md
  memory.md
  playground/
  reference/
```

如果你想在 project 根目录直接访问源码仓库，可以按需手动创建 symlink，例如：

```bash
ln -s ../../core/ChatTool ~/workspace/arxiv-demo/projects/04-20-arxiv-explore-tool/ChatTool
```

这不是必需步骤，只是为了缩短路径。

## 4. 写 PRD.md

`PRD.md` 是 `chatloop` 的主入口。它应该只写稳定需求、范围、约束、交付物和完成标准。

下面是一份最小可用示例：

```md
## 背景

需要在 `core/ChatTool` 中新增一个 `arxiv-explore` 工具，支持通过 ChatTool CLI 搜索 arXiv 论文，并输出结构化结果。

## 目标

- 提供一个可调用的 `chattool arxiv-explore` 入口。
- 支持按关键词搜索论文。
- 输出标题、作者、发布时间、摘要和 arXiv 链接。

## 范围

- 仅实现最小可用搜索能力。
- 仅处理 arXiv 官方公开接口。
- 补齐与该命令直接相关的文档和测试。

## 非目标

- 暂不实现下载 PDF。
- 暂不实现复杂排序和多源聚合。

## 交付物

- CLI 命令实现。
- 相关测试。
- 对应文档更新。

## 完成标准

- 用户可以通过 CLI 传入关键词完成搜索。
- 输出包含标题、作者、发布时间、摘要和 arXiv 链接。
- 相关测试通过。
- 文档能说明基本用法。

## 待处理问题
```

规则：

- `PRD.md` 不要写阶段性流水账
- 阶段进展写到 `progress.md`
- 局部路径、关键文件、临时结论写到 `memory.md`
- 如果当前没有歧义，`待处理问题` 区块保留为空

## 5. 启动 Loop

进入 project 根目录后，在 OpenCode 中显式触发：

```text
/chatloop 按当前 PRD 开发 arxiv-explore 工具。先阅读 PRD.md，再检查 memory.md 和 progress.md 是否有补充上下文；随后进入实现、测试和文档更新流程。如果完成标准已满足，输出 <complete>DONE</complete>。
```

不建议只输入很短的 `/chatloop ?`。更好的方式是给一条清晰任务指令，让第一轮就覆盖主链路。

## 6. 启动后会发生什么

`/chatloop ...` 触发后，插件会做这些事：

1. 从当前目录向上寻找最近的 `PRD.md`
2. 把这个目录视为当前 project 根目录
3. 在 project 根目录下写状态文件：`.opencode/chatloop.local.md`
4. 在 project 根目录下追加事件记录：`chatloop.events.log`
5. 把你的初始消息原样发给当前 session，或在没有消息时构造一条 fresh-start prompt
6. 每当模型进入 idle，重新发一条 fresh-start prompt，让模型重新从 `PRD.md` 理解任务
7. 如果模型输出 `<complete>DONE</complete>`，停止 continuation

换句话说，`chatloop` 不依赖之前的聊天上下文持续滚动，而是不断回到 `PRD.md` 这个主入口。

## 7. 如何判断正在生效

先执行：

```text
/chatloop-status
```

正常情况下你会看到：

- 当前解析到的 `Project root`
- `PRD entry`
- `State file`
- `Events file`
- 当前是否 active

你还可以直接查看 project 根目录下的：

```text
.opencode/chatloop.local.md
chatloop.events.log
```

`chatloop.events.log` 是最直接的事件记录，例如：

```text
2026-04-20T10:00:00.000Z | INFO  | chatloop.start | session=abc123 | project=/home/me/workspace/arxiv-demo/projects/04-20-arxiv-explore-tool cwd=/home/me/workspace/arxiv-demo/projects/04-20-arxiv-explore-tool maxIterations=20
2026-04-20T10:01:12.000Z | INFO  | chatloop.idle | session=abc123 | restarting fresh iteration=2
2026-04-20T10:03:34.000Z | INFO  | chatloop.complete | session=abc123 | assistant emitted completion marker
```

## 8. 常见调试动作

查看状态：

```text
/chatloop-status
```

查看帮助：

```text
/chatloop-help
```

停止当前 loop：

```text
/chatloop-stop
```

查看事件记录：

```bash
tail -f chatloop.events.log
```

## 9. 推荐工作方式

- 先把 `PRD.md` 写清楚，再启动 `/chatloop`
- 让 `PRD.md` 只保留稳定需求，不要把过程细节塞进去
- 每次遇到新阶段或重要决定，更新 `progress.md`
- 如果路径很多、上下文复杂，用 `memory.md` 记录关键入口
- 如果需求有歧义，优先在 `PRD.md` 的 `待处理问题` 中显式列出，而不是让模型默默猜

## 10. 一句话流程

最短流程就是：

1. `chattool setup opencode --install-only --plugin chatloop`
2. `chattool setup workspace ~/workspace/demo --with-opencode-loop`
3. 在 `projects/` 下创建 project 并写好 `PRD.md`
4. 进入 project 根目录执行 `/chatloop ...`
5. 用 `/chatloop-status` 和 `chatloop.events.log` 调试是否生效
6. 等模型输出 `<complete>DONE</complete>` 正常结束
