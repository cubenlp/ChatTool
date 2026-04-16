# Agent Loop 插件调研：OpenCode、Claude Code、Codex 现状与可复用思路

这篇文章记录一次比较具体的调研：如果我们希望给终端 Agent 增加“自动续推 / loop”能力，现成生态里有哪些方案是开箱即用的，哪些方案更适合参考后自己做一层封装。

调研对象主要有三类：

- **OpenCode**：以 `opencode-auto-loop` 为代表的 plugin / session API 路线
- **Claude Code**：以 loop plugin 和 stop hook 为代表的原生插件路线
- **Codex**：以 hooks + skills + support files 为代表的 support-files 路线

目标不是列一个“谁功能最多”的清单，而是回答三个更实际的问题：

1. 有没有 **开箱即用** 的安装方式
2. 交互体感能不能尽量接近原始 TUI
3. 如果我们最后要在 OpenCode 里自己封装一层，最值得复用哪种思路

---

## 一、先说结论

如果优先级是“先找能直接装来用的”，结论非常明确：

- **Claude Code 生态里现成 loop 插件最多，也最接近开箱即用**
- **Codex 生态里有成熟 loop 项目，但多数不是 marketplace 一键装完就能跑**
- **OpenCode 现在最像现成方案的是 `opencode-auto-loop`，但实际加载链路仍需要额外验证**

如果优先级是“交互过程尽量和原始用法一致”，结论也很明确：

- **plugin / hook 型方案的体感最好**
- **外部 runner 次之**
- **PTY 接管终端的方案最容易把体验做坏**

这也是为什么我们最后更倾向于：

- 先调研现成 plugin
- 真要自己做，也优先做 **OpenCode 内部命令 + 会话事件续推**
- 不继续把大量精力压在 PTY 劫持上

---

## 二、OpenCode 现成方案：`opencode-auto-loop`

目前最接近现成方案的是：

- `opencode-auto-loop`

从它的 README 看，设计目标非常直接：

- 在 OpenCode 配置里加一条 `plugin`
- 重启 OpenCode
- 插件第一次运行时自行安装 `commands/` 与 `skills/`

看起来像这样：

```json
{
  "plugin": ["opencode-auto-loop"]
}
```

后续 loop 续推时，它并不是通过终端输入模拟，而是直接走 OpenCode 内部 session API，等 session 进入 idle 后，再调用类似下面的接口追加消息：

```ts
client.session.promptAsync({
  path: { id: sessionId },
  body: {
    parts: [{ type: "text", text: continuationPrompt }],
  },
})
```

这条路线的优点非常大：

- 不劫持终端字符流
- 不污染输入框
- 不依赖 TUI 的重绘细节
- 从产品体验上更接近“原生支持的 loop”

但这次实际验证也暴露了一个关键事实：

- **只把 `plugin: ["opencode-auto-loop"]` 写进配置，还不足以保证本机真的能顺利加载它**

如果本地环境里插件包解析不稳定，结果就会变成：

- 启动时卡顿
- 命令和能力没有真正出现

所以对 OpenCode 来说，`opencode-auto-loop` 当前更准确的定位是：

- **最值得优先验证的现成方案**
- 但还不能直接下结论说“这就已经是完全开箱即用”

---

## 三、Claude Code：现成 loop 插件最成熟

Claude Code 这条线最有价值，因为它已经有非常明确的 plugin / hook 模式。

我们重点看了两个方向。

### 1. `claude-devloop`：最像“原生 loop plugin”

这个项目的结构非常清晰：

```text
claude-loop/
├── .claude-plugin/
│   └── marketplace.json
└── loop/
    ├── .claude-plugin/plugin.json
    ├── commands/
    │   ├── start.md
    │   └── stop.md
    ├── hooks/
    │   ├── hooks.json
    │   ├── claim-hook.sh
    │   └── stop-hook.sh
    └── scripts/
        ├── setup-loop.sh
        └── stop-loop.sh
```

它的核心思路不是外部重启 Claude，而是：

1. 通过 `/loop:start` 创建 loop 状态
2. 通过 `UserPromptSubmit` hook 把当前 session 和状态文件绑定
3. 在 Claude 尝试退出时，由 `Stop` hook 拦截
4. 再把原 prompt 带着 iteration 信息重新喂回去

这个设计非常值得重视，因为它几乎精准满足了“交互体感尽量和原始用法一致”的要求：

- 还是原来的 Claude TUI
- 只是新增一个本地命令
- loop 的接管点发生在宿主原生 hook 上

它还有一个很重要的设计：**每个 session 独立状态文件**。

状态文件大概像这样：

```yaml
---
active: true
iteration: 3
max_iterations: 10
completion_promise: "All tests passing"
transcript_path: "/path/to/session/transcript.jsonl"
term_session_id: "..."
started_at: "2024-01-01T12:00:00Z"
---

Your task prompt here
```

这套结构很适合后续参考到 OpenCode：

- 本地命令触发
- 每 session 独立 state file
- 明确的 completion promise
- stop 事件续推

### 2. `ralph-claude-code`：不是 plugin，但策略很完整

`ralph-claude-code` 走的是另一条路线：

- 外部 runner
- shell orchestration
- 状态目录 `.ralph/`
- response analyzer / circuit breaker / rate limiting / session continuity

它的价值不在“交互体感”，而在“控制策略很完整”。

如果从实现经验角度看，最值得借鉴的是：

- dual-condition exit gate
- no-progress / stuck loop 检测
- rate limiting
- circuit breaker
- 可读的状态文件和日志

它不适合直接当 OpenCode 的实现模板，但非常适合给内部状态机提供经验。

---

## 四、Codex：support files 和 hooks 比 plugin 更重要

Codex 这条线最值得看的不是 marketplace 风格 plugin，而是 **hooks + skills + repo-local support files**。

重点项目是：

- `autonomous-loop`

它采用“两层安装”模型：

### 1. Machine bootstrap

写到机器全局：

- `$CODEX_HOME/hooks.json`
- `$CODEX_HOME/skills/autonomous-loop/SKILL.md`
- `$CODEX_HOME/autoloop/machine.json`

### 2. Repo install

写到当前仓库：

- `.codex/autoloop.project.json`
- `.codex/hooks.json`
- `.agents/skills/autonomous-loop/SKILL.md`

然后它不只是“不断继续 prompt”，而是维护一份更严格的 contract：

- objective
- required tasks
- evidence
- gate profile

在每次 `Stop` hook 时重新验证：

- 文件系统证据
- trusted commands
- 是否允许 release / block / hard-stop

这套方式非常稳，但明显也更重。

如果只看“有没有现成 loop 方案”，Codex 生态是有的；如果只看“是不是最容易直接装”，那它就不如 Claude plugin 轻。

---

## 五、外部 runner 能不能做？可以，但体感通常不如 plugin

在这次调研之前，我们自己也试过一条路线：

- 用 `ralph.py` 之类的外部 PTY 控制器
- 启动 OpenCode
- 透传输入输出
- 在静默时自动注入 prompt

这条路线不是完全错误，但它有一个核心问题：

- **它太靠近终端字符流了**

一旦靠近这一层，就容易踩到：

- TUI alt-screen 重绘
- resize 同步
- 输入回显
- 鼠标事件和控制序列
- 特殊命令泄漏
- 原始日志难以阅读

从最终产品体验看，这类方案很难做到真正“像原始用法”。

所以更现实的判断是：

- **外部 runner 更适合做概念验证或通用编排器**
- **如果目标是交互过程看起来像原生 TUI，就应该优先走 plugin / hook / session API**

---

## 六、如果以后要在 OpenCode 自己做，最值得复用什么

如果 OpenCode 现成的 `opencode-auto-loop` 最终不能直接满足需求，我们还是可能自己封装一层。

这时候最值得复用的，不是某一个项目的全部实现，而是三套思路的组合：

### 1. 命令与状态模型：参考 `claude-devloop`

最值得抄的点：

- `/loop:start` 这种本地命令入口
- 每 session 一个 state file
- frontmatter + body 的状态格式
- session isolation
- `start` / `stop` 作为明确控制面

### 2. 会话续推方式：参考 `opencode-auto-loop`

最值得抄的点：

- 不碰 PTY/TUI 输入劫持
- 直接在 `session.idle`、`session.compacted`、`session.error` 等事件上做续推
- 用内部 `promptAsync` 之类的 API 注入文本

### 3. 风险控制：参考 `autonomous-loop` 和 `ralph-claude-code`

最值得抄的点：

- fail-closed 而不是 fail-open
- no-progress / stale state 清理
- rate limit / max iteration
- contract / gate 可以作为第二阶段增强

---

## 七、我们自己验证过的 `ralph.py` 还留下了哪些有效结论

虽然 `ralph.py` 这条 PTY 路线最后没有继续走，但它并不是白做了。

它至少验证了几条非常关键的产品语义：

1. **需要区分 `chat` 和 `loop` 两种模式**
2. **prompt 文件应属于控制器，而不是直接暴露给模型**
3. **需要区分“用户主动暂停”和“模型/系统停滞”**
4. **日志应该优先记录动作，而不是原始 PTY 流**
5. **loop 必须由一个显式命令触发，而不是靠自然语言猜测**

这些都和现成项目的设计高度一致，说明方向本身是对的，只是控制层级选错了。

---

## 八、最终建议

如果把问题拆成两个任务：

### 任务 A：先找能直接安装来用的

优先级建议：

1. 先验证 `opencode-auto-loop` 的真实安装与加载链路
2. Claude 生态优先参考 `claude-devloop`
3. Codex 生态优先参考 `autonomous-loop`

### 任务 B：如果最后要自己做一层封装

建议不要从 PTY 继续做，而是：

- 用 OpenCode plugin / command / session API
- 命令与状态模型参考 `claude-devloop`
- 续推方式参考 `opencode-auto-loop`
- 风控策略参考 `autonomous-loop` 与 `ralph-claude-code`

一句话总结：

> **开箱即用优先看 Claude，原生体验优先做 plugin/hook，OpenCode 自己做时最值得复用的是 `claude-devloop` 的命令+状态模型，以及 `opencode-auto-loop` 的会话事件续推。**
