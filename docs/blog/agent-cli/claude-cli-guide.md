# Claude Code CLI 教程：交互会话、`--print`、权限模式与会话恢复

这一篇讲 **Claude Code**。

和 Codex、OpenCode 一样，Claude Code 也是一个“既能交互、也能脚本化”的终端 Agent。但它的命令行设计有两个非常明显的特点：

- 默认直接进入 **交互会话**
- 非交互模式不走单独子命令，而是靠 `-p/--print`

本文内容基于本机在 **2026-03-27** 执行 `claude --help`、`claude auth --help`、`claude auth login --help`、`claude agents --help`、`claude mcp --help` 的结果整理，重点讲终端里怎么用。

---

## 先理解 Claude 的两种工作方式

总帮助第一句就把它说清楚了：

> Claude Code 默认启动交互式会话；如果要非交互输出，用 `-p/--print`。

也就是说，你先不用找 `exec` 之类的子命令，先记住这两类入口就够了：

```bash
claude
claude -p "your prompt"
```

如果只记一句判断标准，可以记这个：

> **想持续协作，用 `claude`；想一次出结果、接管道或进脚本，用 `claude -p`。**

---

## 第一步：先处理认证

Claude 把认证放在 `auth` 子命令下。

查看当前认证状态：

```bash
claude auth status
```

登录：

```bash
claude auth login
```

`claude auth login --help` 里能看到几种登录路线：

```bash
claude auth login --claudeai
claude auth login --console
claude auth login --email you@example.com
claude auth login --sso
```

其中：

- `--claudeai` 走 Claude 订阅体系
- `--console` 走 Anthropic Console / API 计费体系
- `--sso` 强制 SSO 登录流程

登出：

```bash
claude auth logout
```

---

## 交互式使用：`claude`

直接启动当前目录下的交互会话：

```bash
claude
```

直接附带一个初始 prompt：

```bash
claude "先阅读这个仓库，再告诉我主入口在哪里"
```

### 会话恢复

继续当前目录最近一次会话：

```bash
claude --continue
```

按 session id 恢复：

```bash
claude --resume <SESSION_ID>
```

恢复时分叉成新会话：

```bash
claude --continue --fork-session
```

给当前会话起名字：

```bash
claude -n docs-review
```

### 指定模型和推理强度

```bash
claude --model sonnet
claude --model claude-sonnet-4-6 --effort high
```

帮助里给出的模型示例说明，它既支持别名，也支持完整模型名。

---

## 非交互模式：`claude -p`

Claude 的非交互入口不是单独命令，而是 `-p/--print`。

最基础的用法：

```bash
claude -p "总结当前目录下的文档结构"
```

这类模式适合：

- shell 管道
- 一次性脚本调用
- CI 生成文本结果
- 想拿结构化输出

### 输出格式

```bash
claude -p --output-format text "..."
claude -p --output-format json "..."
claude -p --output-format stream-json "..."
```

### 结构化输出

```bash
claude -p --json-schema '{"type":"object","properties":{"summary":{"type":"string"}},"required":["summary"]}' "总结这个 diff"
```

### 从流式输入读消息

```bash
claude -p --input-format stream-json --output-format stream-json
```

### 不保存会话

```bash
claude -p --no-session-persistence "临时生成一段说明"
```

### 控制预算

```bash
claude -p --max-budget-usd 0.50 "先做一次简短代码审查"
```

如果你平时会把模型输出接进别的脚本，Claude 这套 `--print + 输出格式` 的路线是它最关键的能力之一。

---

## 权限控制：Claude 的重点之一

Claude 的帮助信息里，权限相关参数非常多。这说明它很强调“当前会话能做什么、是否要你批准”。

### 直接指定 permission mode

```bash
claude --permission-mode default
claude --permission-mode acceptEdits
claude --permission-mode plan
claude --permission-mode auto
claude --permission-mode dontAsk
claude --permission-mode bypassPermissions
```

这些模式的核心区别，可以先粗略理解为：

- `default`：按默认策略逐步确认
- `acceptEdits`：编辑更宽松，但不是全放开
- `plan`：先规划，执行更克制
- `auto`：更自动化
- `dontAsk` / `bypassPermissions`：更少询问，风险更高

### 工具白名单 / 黑名单

```bash
claude --allowedTools "Bash(git:*) Edit"
claude --disallowedTools "Bash(rm:*)"
```

### 限定可用工具集合

```bash
claude --tools "default"
claude --tools "Bash,Edit,Read"
claude --tools ""
```

### 显式开放额外目录

```bash
claude --add-dir ../shared-docs
```

如果你在意本机权限边界，Claude 这套参数比“一个简单开关”要细得多。

---

## 常见上下文控制参数

除了权限和输出方式，Claude 还提供了不少“注入上下文”的入口。

### 系统提示词

```bash
claude --system-prompt "你是一个严格的代码审查助手"
claude --append-system-prompt "优先关注 CLI 行为回归"
```

### settings 与 settings source

```bash
claude --settings ./claude-settings.json
claude --setting-sources user,project,local
```

### bare 模式

```bash
claude --bare
```

`--bare` 的帮助说明非常激进，它会跳过 hooks、LSP、plugin sync、自动发现 `CLAUDE.md` 等一整套外围能力，更像“最小运行模式”。

---

## worktree、tmux、IDE：Claude 的环境集成能力

Claude 有几项很明显偏工程化的参数。

### 创建独立 worktree

```bash
claude --worktree
claude --worktree feature-docs
```

### 配合 tmux

```bash
claude --worktree feature-docs --tmux
```

### 自动连接 IDE

```bash
claude --ide
```

这些参数说明 Claude 不只是“在当前 shell 里回答你”，而是试图把会话组织成一个更完整的开发工作环境。

---

## MCP 与 Agents

Claude 把 MCP 和 agents 都做成了一级能力。

### 列出 configured agents

```bash
claude agents
```

### 会话里直接指定 agent

```bash
claude --agent reviewer
```

或者临时注入自定义 agents：

```bash
claude --agents '{"reviewer":{"description":"Reviews code","prompt":"You are a code reviewer"}}'
```

### 管理 MCP

```bash
claude mcp list
claude mcp add my-server -- npx my-mcp-server
claude mcp serve
```

从帮助里还能看到它支持：

- HTTP MCP server
- 带 header 的远程 MCP
- stdio MCP server
- 从 Claude Desktop 导入 MCP

如果你的工作流里已经 heavily 依赖 MCP，这部分会比纯聊天更重要。

---

## 几个实用命令模板

### 1. 在当前仓库里开交互会话

```bash
claude "先阅读仓库，再告诉我最值得优先看的文件"
```

### 2. 一次性输出结果

```bash
claude -p "总结 docs/blog/agent-cli 下每篇文章的主题"
```

### 3. JSON 输出

```bash
claude -p --output-format json "输出一个包含 summary 和 risks 的 JSON"
```

### 4. 恢复上次会话并分叉

```bash
claude --continue --fork-session
```

### 5. 开一个更克制的规划模式

```bash
claude --permission-mode plan "先规划这次重构要改什么"
```

---

## 怎么选用法

如果只按命令行工作方式来分，Claude 的决策很简单：

- 持续交互：`claude`
- 一次性执行：`claude -p`
- 继续历史：`claude --continue` 或 `claude --resume`
- 更细权限控制：`--permission-mode`、`--tools`、`--allowedTools`
- 更强环境集成：`--worktree`、`--tmux`、`--ide`

Claude CLI 的关键不是子命令多，而是**顶层参数非常密**。你一旦把 `-p`、会话恢复、权限模式和上下文注入这几块理顺，终端里的使用感受会稳定很多。
