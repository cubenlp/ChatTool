# Codex CLI 教程：终端交互、exec、review 与会话续跑

这一篇先只讲 **Codex**。

如果你平时主要在终端里工作，Codex 的核心价值不是“能聊天”，而是它把**交互式协作**、**非交互执行**、**代码 Review** 和 **会话续跑** 放进了同一个 CLI 里。

本文内容基于本机在 **2026-03-27** 执行 `codex --help`、`codex exec --help`、`codex review --help`、`codex resume --help`、`codex completion --help`、`codex login --help` 的结果整理，重点讲“怎么用”，不是单纯翻译帮助信息。

---

## 先理解 Codex 的两种入口

`codex` 的总入口其实有两种工作方式：

```bash
codex [OPTIONS] [PROMPT]
codex [OPTIONS] <COMMAND> [ARGS]
```

这意味着：

- 不带子命令时，默认进入 **交互式 CLI**
- 带上子命令时，进入明确的任务模式，比如 `exec`、`review`、`resume`

如果你只记一个原则，可以记这个：

> **想边聊边改，就用 `codex`；想脚本化或单次执行，就用 `codex exec`。**

---

## 第一步：先登录

第一次使用先完成认证。

### 交互登录

```bash
codex login
```

查看当前登录状态：

```bash
codex login status
```

### 用 API Key 登录

如果你已经有环境变量，也可以直接从标准输入读入：

```bash
printenv OPENAI_API_KEY | codex login --with-api-key
```

这类方式适合远程机、容器、CI 或你不想在提示里手输密钥的场景。

---

## 交互式使用：最像“终端里的 Agent”

直接运行：

```bash
codex
```

或者带一个初始任务：

```bash
codex "帮我分析这个仓库的 CLI 结构"
```

这种模式下，Codex 会进入交互式会话。你可以持续追加需求，让它查看文件、运行命令、修改代码。

### 常用交互参数

指定工作目录：

```bash
codex -C /path/to/project
```

附带图片作为初始输入：

```bash
codex -i ./error.png "帮我分析这张报错截图"
```

启用联网搜索：

```bash
codex --search "帮我核对这个第三方库的最新官方文档"
```

关闭 alternate screen，保留终端滚动历史：

```bash
codex --no-alt-screen
```

这个参数在 `tmux`、`zellij` 或你需要保留完整 scrollback 时很实用。

---

## 会话续跑：不要每次都从头开始

Codex 把交互会话保存成可恢复的 session，因此你不用每次重新解释上下文。

继续最近一次会话：

```bash
codex resume --last
```

按 session id 恢复：

```bash
codex resume <SESSION_ID>
```

恢复时顺带补一句新指令：

```bash
codex resume --last "继续刚才那篇文档，补上常见错误排查"
```

`codex` 顶层帮助里还提供了 `fork` 命令，适合你想从已有上下文分叉出另一条处理路线时使用。

---

## 非交互执行：把 Codex 当成一次性命令

如果你不需要持续对话，而是想让它完成一次明确任务，用 `exec`：

```bash
codex exec "总结这个仓库里所有 blog 文档的主题"
```

它的适用场景很明确：

- Shell 脚本中一次性调用
- CI 中生成报告
- 批处理型任务
- 想把最终输出写进文件或 JSON 流

### 从 stdin 读任务

```bash
printf '请总结当前 git diff 的风险点\n' | codex exec -
```

### 输出最后一条消息到文件

```bash
codex exec "为 docs/blog 写一段摘要" -o /tmp/codex-last.txt
```

### 输出 JSONL 事件流

```bash
codex exec --json "分析当前目录结构"
```

### 不持久化会话

```bash
codex exec --ephemeral "临时看一下这个目录的用途"
```

### 在非 Git 目录运行

```bash
codex exec --skip-git-repo-check "解释这个目录里有哪些文件"
```

如果你在做自动化接入，`exec` 一般是第一选择。

---

## 代码 Review：直接走专门子命令

Codex 单独提供了 `review`，它不是普通聊天，而是专门面向代码审查。

检查当前未提交改动：

```bash
codex review --uncommitted
```

对比某个基线分支：

```bash
codex review --base main
```

审查某一个 commit：

```bash
codex review --commit <SHA>
```

补充自定义审查要求：

```bash
codex review --base main "重点看 CLI 行为变化和文档是否同步"
```

如果你的日常流程里已经有 `git diff`、`git show`、PR 自查，`codex review` 很适合插在提交前或发 PR 前。

---

## 批准与沙箱：这是命令行 Agent 的关键

Codex 不是只输出文字，它会尝试执行命令。所以你需要明确它在本机上的权限边界。

### 沙箱模式

```bash
codex -s read-only
codex -s workspace-write
codex -s danger-full-access
```

三种模式可以粗略理解为：

- `read-only`：只读，适合调研和只看不改
- `workspace-write`：可修改工作区，适合常规开发
- `danger-full-access`：完全放开，适合你已经在外层容器或沙箱里兜底

### 批准策略

```bash
codex -a untrusted
codex -a on-request
codex -a never
```

- `untrusted`：只放行可信命令，危险动作需要你批
- `on-request`：模型自己判断何时申请批准
- `never`：不向你申请，失败直接返回给模型

帮助信息里还提供了两个快捷选项：

```bash
codex --full-auto
codex --dangerously-bypass-approvals-and-sandbox
```

其中 `--full-auto` 是偏实用的默认自动执行方案；而 `--dangerously-bypass-approvals-and-sandbox` 名字已经说明问题了，只该出现在你非常确定外层环境已经隔离好的地方。

---

## 影响体验的几个高频参数

除了基础命令，下面这些参数最值得优先记住。

### 选择模型

```bash
codex -m gpt-5
```

### 使用 profile

```bash
codex -p default
```

适合把常用模型、权限策略、目录等配置进 `~/.codex/config.toml` 后复用。

### 临时覆写配置

```bash
codex -c 'model="gpt-5"' -c shell_environment_policy.inherit=all
```

`-c` 支持 dotted path，可以做细粒度覆写。

### 启用或关闭 feature flag

```bash
codex --enable some_feature
codex --disable some_feature
```

### 走本地开源模型

```bash
codex --oss
codex --oss --local-provider ollama
```

如果你本地已经跑着 LM Studio 或 Ollama，这条路线会比较顺。

### 扩展可写目录

```bash
codex --add-dir ../shared-assets
```

当工作目录之外还有几个确实要写入的路径时，这个参数很有用。

---

## Shell 补全：让它更像一个成熟命令

Codex 自带 completion 生成功能。

例如生成 zsh 补全：

```bash
codex completion zsh
```

支持的 shell 有：

- `bash`
- `elvish`
- `fish`
- `powershell`
- `zsh`

如果你高频使用 `exec`、`review`、`resume` 这些子命令，补全会明显减少记忆负担。

---

## 几个实用命令模板

如果你想马上上手，可以直接从这几条开始。

### 1. 在当前仓库里进入交互协作

```bash
codex "先阅读这个仓库，再告诉我最关键的开发入口"
```

### 2. 指定目录执行一次性任务

```bash
codex exec -C /path/to/repo "总结 src/ 下各模块职责"
```

### 3. 对当前未提交改动做审查

```bash
codex review --uncommitted "优先关注行为回归和漏掉的文档"
```

### 4. 恢复上一次工作

```bash
codex resume --last
```

### 5. 保留终端历史、同时允许联网

```bash
codex --no-alt-screen --search
```

---

## 怎么选交互方式

如果你还在犹豫该用哪条命令，可以直接按下面分：

- 想持续对话、逐步修改代码：`codex`
- 想一次性完成任务并收结果：`codex exec`
- 想专门看代码问题：`codex review`
- 想接着上次工作继续：`codex resume`

这也是 Codex CLI 最实用的地方：**不是一个命令包打天下，而是把不同工作流拆成了几个边界清晰的入口。**

---

## 结语

如果只从帮助信息看，Codex 像是一个“命令很多”的 CLI；但真正上手后，你会发现它其实只是在解决四件事：

- 怎么进入交互式协作
- 怎么做一次性自动执行
- 怎么审代码
- 怎么续上历史上下文

把这四件事用顺以后，Codex 在终端里的使用体验会稳定很多。

下一篇再继续拆 **OpenCode** 和 **Claude** 的命令行交互方式，最后再对比三者各自适合的工作流。
