# Happy Coder 调研：把手机/网页远程控制接进 coding agent，与自建 relay 怎么配合

这篇文章不是在说 ChatTool 已经内置了一个完整的 Happy 替代品。它更像是一份调研记录：

- `./happy` 项目到底是什么
- 它和 ChatTool 现在已经有的能力怎么拼起来
- 如果你想自建一套 relay / server / workspace，哪些地方已经能复用，哪些地方仍然是外部系统

## 1. 先说结论

Happy 的核心不是“又一个模型提供商”。

它解决的是另一类问题：

- 让你在手机、网页、桌面之间切换控制 Claude Code / Codex / Gemini 之类 coding agent
- 通过 daemon + server + app 的组合，把本地 agent 会话安全地接到远端界面
- 所有消息在离开设备前先做端到端加密

也就是说，Happy 更像一层 **remote control plane**，不是一层 **LLM provider abstraction**。

而 ChatTool 现在擅长的是另一边：

- 配置 OpenAI-compatible `base_url`
- 配置 Codex / OpenCode / Claude Code 这些 CLI
- 初始化 workspace / playground 协作结构
- 组织 GitHub / skills / setup / env 的本地工作流

所以这两者并不冲突，反而天然能拼起来。

## 2. `./happy` 项目是什么

从仓库根下的 `happy/README.md` 可以直接看出它的定位：

- Mobile and Web Client for Claude Code & Codex
- 支持 `happy claude`、`happy codex`、`happy gemini`
- 也支持 `happy acp opencode`，即任意 ACP-compatible agent

它是一个 monorepo，主要包含：

- `packages/happy-cli`
- `packages/happy-app`
- `packages/happy-agent`
- `packages/happy-server`

最关键的是它不是单一 CLI，而是三层结构：

1. **happy-cli**：本地代理层，负责包装 Claude/Codex/Gemini 这些 agent CLI
2. **happy-server**：后端服务，负责 session / machine / auth / push / sync
3. **happy-app / web**：移动端和网页端，用来远程查看和控制会话

## 3. Happy CLI 的工作方式

`happy/packages/happy-cli/src/index.ts` 暴露出来的主命令可以看出它的工作方式：

- `happy`
- `happy codex`
- `happy gemini`
- `happy resume`
- `happy daemon ...`
- `happy auth ...`
- `happy connect ...`

这说明 Happy CLI 不是简单“代替 codex”的 wrapper，而是一个 **本地 session 编排器**。

核心特征有几个：

### 3.1 它有 daemon

`happy/packages/happy-cli/src/daemon/run.ts` 说明 daemon 是常驻进程，负责：

- 机器注册
- 会话追踪
- RPC 控制
- 和后端 server 保持 WebSocket 长连接

所以 Happy 的“远程接管”不是靠把终端直接暴露出去，而是靠 daemon 做本地编排、server 做同步、app 做控制。

### 3.2 它有独立认证体系

`happy/packages/happy-cli/src/ui/auth.ts` 说明 Happy 不是拿 GitHub token 直接登录，而是：

- 生成本地密钥对
- 通过 Happy server 发起 auth request
- 用移动端或网页端批准
- 之后拿回加密材料和 server token

这意味着：

- Happy server 不是可选装饰，它是官方远程模式的核心一环
- `happy auth login` 是必须动作，不是像 `setup codex` 那样只写本地 config 就够了

### 3.3 它支持自定义 server/web URL

`happy/packages/happy-cli/src/configuration.ts` 里明确读这些变量：

- `HAPPY_SERVER_URL`
- `HAPPY_WEBAPP_URL`
- `HAPPY_HOME_DIR`

默认分别是：

- `https://api.cluster-fluster.com`
- `https://app.happy.engineering`
- `~/.happy`

所以 Happy 从架构上就是支持“官方托管模式”和“自定义部署模式”的。

## 4. 自建到底指什么

如果说“自建 Happy”，要分清两种完全不同的东西。

### 4.1 自建 OpenAI-compatible relay

这是模型接入层。

它影响的是：

- `OPENAI_API_BASE`
- `OPENAI_API_KEY`
- `OPENAI_API_MODEL`

这层和 ChatTool 非常契合，因为 ChatTool 本来就在管理这些配置。

### 4.2 自建 Happy server / webapp

这是 Happy 自己的远程会话基础设施。

它影响的是：

- `HAPPY_SERVER_URL`
- `HAPPY_WEBAPP_URL`
- `happy auth login`
- daemon 与 server 的同步

这层是 Happy 体系本身的事，ChatTool 只能帮你“接进去”，不能冒充已经实现。

## 5. ChatTool 现在已经能复用什么

这里就是这次调研最有价值的部分。

### 5.1 ChatTool 已经能管 OpenAI-compatible relay

当前仓库所有和 OpenAI-compatible 相关的主线都已经存在：

- `setup codex`
- `setup opencode`
- `OpenAIConfig`
- `Chat(api_base=...)`

所以如果你的 happy coder 路线里需要一套 relay，这一层完全可以由 ChatTool 负责。

### 5.2 ChatTool 已经能管 workspace / playground

Happy 解决的是“怎么远程控制 agent”。
ChatTool 解决的是“怎么组织本地协作结构”。

这两者可以天然叠加：

- Happy 负责跨设备接管 session
- ChatTool 负责 `workspace` / `playground` / `reports` / `knowledge`

### 5.3 ChatTool 已经有代理/暴露的现成支点

仓库里没有 Happy server 的实现，但已经有两类非常接近的能力：

- `docs/env/nginx_proxy.md`：反向代理文档
- `setup frp` / `docs/tools/frp.md`：内网穿透与服务暴露

所以如果你要做“自建 Happy server / relay 的部署实践”，这部分不需要从零开始重新发明文档结构。

## 6. ChatTool 里最合理的 happy 入口应该是什么

基于上面的调研，最合理的第一步不是在 ChatTool 里复刻 Happy server，而是做一个：

```bash
chattool setup happy
```

它做的事情应该是：

1. 安装 `happy` CLI
2. 收集或复用：
   - `HAPPY_SERVER_URL`
   - `HAPPY_WEBAPP_URL`
   - `HAPPY_HOME_DIR`
   - `OPENAI_API_BASE`
   - `OPENAI_API_KEY`
   - `OPENAI_API_MODEL`
3. 把 Happy 的 server/webapp 配置存成一份 profile
4. 把 OpenAI-compatible relay 配置也存成一份 profile
5. 打印推荐的下一步：
   - `chattool setup codex -e happy`
   - `chattool setup opencode -e happy`
   - `chattool setup workspace ...`
   - `happy auth login`

这条路线的好处是：

- 复用现有 setup 框架
- 不声称 ChatTool 已经实现 Happy server
- 但又能把“happy coder + relay + workspace”真的串起来

## 7. 官方模式与自建模式

如果做成 `setup happy`，建议明确区分两种模式。

### 官方模式

- `HAPPY_SERVER_URL=https://api.cluster-fluster.com`
- `HAPPY_WEBAPP_URL=https://app.happy.engineering`

然后继续：

```bash
happy auth login
```

### 自建模式

如果你自己部署了 Happy server / webapp，则配置：

- `HAPPY_SERVER_URL=https://happy.example/api`
- `HAPPY_WEBAPP_URL=https://happy.example/app`

如果你还自建了 OpenAI-compatible relay，则另外配置：

- `OPENAI_API_BASE=https://relay.example/v1`
- `OPENAI_API_KEY=...`
- `OPENAI_API_MODEL=...`

这两层不要混淆：

- Happy server 是远程控制平面
- OpenAI relay 是模型访问平面

## 8. 一句话总结

这次调研最关键的结论是：

> Happy 解决的是“远程控制 coding agent”，ChatTool 解决的是“本地配置、relay、workspace 和 setup 编排”。

因此，最值得做的不是“让 ChatTool 假装自己实现了 Happy”，而是：

> 用现有的 setup / config / workspace 框架，把 Happy 官方模式、自建 server 模式、自建 relay 模式，变成一条可复用的 happy coder 引导入口。
