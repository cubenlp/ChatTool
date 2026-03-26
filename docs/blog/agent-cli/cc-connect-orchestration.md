# cc-connect 编排教程：多智能体协作是什么形式，能不能在飞书群里工作

这一篇专门讲 **cc-connect 的编排能力**。

前面那篇 [cc-connect 教程](./cc-connect-guide.md) 主要讲的是安装、配置和基本命令；这一篇只回答三个更具体的问题：

1. `cc-connect` 在多智能体之间的“编排”到底是什么形式？
2. 它是不是那种自动任务分发、自动规划的多 Agent 框架？
3. 它能不能在飞书群里工作，群里又是怎么协作的？

本文内容基于本机在 **2026-03-27** 对 `/home/zhihong/Playground/cc-connect` 仓库文档和实现的调研整理，重点参考了：

- `README.md`
- `docs/feishu.md`
- `docs/usage.zh-CN.md`
- `core/relay.go`
- `core/engine.go`
- `platform/feishu/feishu.go`

---

## 第一章：先说结论

先给结论，避免一开始想偏：

> **cc-connect 的多智能体编排，不是 DAG 式自动调度，也不是 AutoGen / CrewAI 那种 planner-driven 编排。**

它目前更接近一种：

> **“群聊上下文里的多机器人绑定 + 显式 relay 转发 + 各自保留独立会话”的编排模式。**

也就是说，cc-connect 的核心不是“帮你自动规划多 agent workflow”，而是：

- 让多个项目 Agent 可以同时在线
- 把这些 Agent 绑定到同一个聊天场景
- 允许一个 Agent 通过 relay 去问另一个 Agent
- 把转发过程和结果回贴到同一个群里，方便人看

如果用工程一点的语言描述，它更像：

- **通信编排层**
- **会话桥接层**
- **群聊协作层**

而不是一个强中心化的“任务图执行器”。

---

## 第二章：它的编排单元不是 agent，而是 project

这是理解 cc-connect 的第一前提。

在 cc-connect 里，最小运行单元不是“一个模型”，而是一个 `project`。每个 project 绑定：

- 一个 agent
- 一个工作目录
- 一个或多个平台

这意味着多智能体编排的真实结构其实是：

```text
project A  -> Claude Code -> workspace A
project B  -> Codex       -> workspace B
project C  -> OpenCode    -> workspace C
```

然后这些 project 再通过平台和 relay 被接进同一个聊天环境。

所以 cc-connect 的多智能体不是“一个大脑下面挂多个 worker”，而更像：

> **多个独立运行的项目 Agent，在同一个消息场里发生协作。**

这点很关键，因为它决定了后面的所有行为：

- 绑定的是 `project name`
- relay 的目标是 `target project`
- 会话也是按 project 分开的

---

## 第三章：它的编排核心，其实是 relay

`README.md` 里把这块叫做：

> Multi-Bot Relay

而实现层里真正负责这件事的是 `RelayManager`。

从实现逻辑看，relay 的核心结构大概是：

1. 在某个群聊里建立绑定关系
2. 记录“这个 chatID 下有哪些 project 参与协作”
3. 当 A 想问 B 时，通过 relay 把消息注入 B 的 engine
4. B 返回结果后，再把结果发回这个群聊

它不是直接让两个 agent 彼此连 socket，而是通过 cc-connect 自己的 engine/relay manager 做中转。

所以它本质上是一种：

> **“由聊天场景驱动的跨 project 消息转发”**

而不是“agent 之间直接 peer-to-peer 自治协商”。

---

## 第四章：具体编排长什么样

如果把它还原成用户能理解的形式，大概是下面这个流程：

### 1. 先让多个项目都跑起来

例如：

- `claudecode`
- `gemini`
- `codex`

这些都作为不同 project 挂在同一个 cc-connect 进程里。

### 2. 在同一个群里绑定它们

文档里给出的典型命令是：

```text
/bind
/bind claudecode
/bind gemini
/bind -claudecode
```

这说明绑定动作是在**聊天里完成**的，不是在本地 shell 里手工改状态。

### 3. 某个 bot 触发 relay

cc-connect 的 CLI 形式是：

```bash
cc-connect relay send --to gemini "你觉得这个架构怎么样？"
```

而 `core/interfaces.go` 里明确写了：

- `<target_project>` 必须是 `/bind` 输出里看到的**精确 project 名**
- relay 会等待目标 bot 返回结果
- 对话过程在群里可见
- 每个 bot 会维护自己的 relay session

### 4. 群里可见地转发与回帖

`core/relay.go` 的实现里，会把这次 relay 的过程显式发回群里，形式近似：

```text
[Claude → Gemini] 你觉得这个架构怎么样？
[Gemini] 我认为可以从模块边界和会话隔离两方面优化……
```

这点很重要，因为它说明 cc-connect 的编排是：

- **显式的**
- **可见的**
- **群聊共享上下文的**

而不是后台静默地跑一堆 agent 再把结果一次性吐回来。

---

## 第五章：它不是自动分工型编排，而是“显式协作型编排”

很多人看到“多智能体编排”这个词，脑子里会自动想到：

- planner 自动拆任务
- reviewer 自动接棒
- coder 自动修复
- tester 自动回归

cc-connect 目前默认不是这个形态。

它更接近下面这种模式：

### 1. 人决定谁和谁协作

你先在群里通过 `/bind` 把哪些项目挂进来。

### 2. 当前 agent 显式调用另一个 agent

要么你手工发命令，
要么 agent 根据注入的 cc-connect 指令，自己学会使用：

```bash
cc-connect relay send --to <target_project> "<message>"
```

### 3. 目标 agent 独立处理，再把结果回传

每个 agent 仍然保留自己的会话和工作目录，不会被揉成一个共享执行上下文。

所以如果一定要给它下定义，我会说：

> **cc-connect 更像“多 agent 协作总线”，不是“多 agent 规划器”。**

这其实是个优点，因为它更稳、更透明，也更容易在真实群聊里落地。

---

## 第六章：relay session 是独立的，不会直接污染主会话

`core/engine.go` 里的 `HandleRelay` 有个很关键的设计：

它给 relay 单独创建 session key，格式近似：

```text
relay:<fromProject>:<chatID>
```

这意味着：

- relay 不是直接复用普通聊天会话
- 每个“来源 project -> 目标 project -> chatID”的关系，都有自己独立的 relay session

这个设计很实用，因为它避免了一个常见问题：

> 群里的主对话和 bot-to-bot 中继消息把同一条 agent 上下文搅乱。

从这里也能看出 cc-connect 的编排风格不是“大一统上下文”，而是：

- 人类会话是人类会话
- relay 会话是 relay 会话
- 每个 target bot 自己保存自己的连续上下文

---

## 第七章：relay 默认会自动放行权限请求

这块是个需要单独提醒的点。

在 `HandleRelay` 的实现里，遇到 `EventPermissionRequest` 时，会直接：

- 自动返回 `allow`

也就是说，**relay 模式下目标 agent 的权限请求默认是自动批准的**。

这背后的设计意图很容易理解：

- relay 是 bot-to-bot 通信
- 如果每次中继都卡在人工审批，群聊编排几乎不可用

但这也意味着：

> 如果你让一个高权限 agent 参与 relay，就要认真考虑它的 mode、工具权限和工作目录边界。

所以从运维角度看，cc-connect 的多智能体编排虽然方便，但不是“零风险自动化”。

---

## 第八章：那它能不能在飞书群里工作？

答案是：

> **能，而且飞书是它的一条主路径，不是边缘支持。**

从文档和实现都能确认这件事。

### 文档层面

`docs/feishu.md` 里明确写了：

- 支持飞书长连接模式
- 无需公网 IP
- 可在群聊里添加机器人使用

### 实现层面

`platform/feishu/feishu.go` 里已经有完整的群聊处理逻辑，包括：

- 识别 `chat_type == "group"`
- 判断是否提及 bot
- 群聊 session key 生成
- 卡片交互回调
- 线程隔离

所以这不是“理论上可以”，而是已经在平台实现里专门做过群聊支持。

---

## 第九章：飞书群里默认怎么工作

默认情况下，飞书群聊不是“看见消息就回复”。

实现里有一个重要判断：

- 如果是群聊
- 且 `group_reply_all` 没开
- 且消息没有提到 bot
- 那就忽略

这意味着飞书群里的默认交互方式是：

> **@机器人后，它才响应。**

这其实是合理默认值，因为如果群里所有消息都进 agent，会非常容易失控。

---

## 第十章：如果你真的想让它在群里全量响应，也可以

飞书平台配置里有一个明确开关：

```toml
group_reply_all = true
```

打开以后，群聊里不再需要 `@机器人` 才触发，所有群消息都可以进入处理流程。

但这个开关适合的场景比较有限，通常只有下面几类才建议开：

- 专门的 bot 工作群
- 人数很少、消息很克制的协作群
- 你明确希望 bot 作为“常驻参与者”

否则普通团队群里开这个，大概率会把 agent 淹死在噪音里。

---

## 第十一章：飞书群聊里，会话还能进一步按 thread 隔离

飞书平台实现里还有一个很值得关注的能力：

```toml
thread_isolation = true
```

这个配置打开后，群聊里的 session key 不再只是：

```text
feishu:<chatID>:<userID>
```

而会优先按 `root_id` / 根消息生成：

```text
feishu:<chatID>:root:<rootID>
```

这意味着什么？

意思是：

> **同一个飞书群里，不同 reply thread 可以拥有各自独立的 agent session。**

这是非常适合群聊编排的，因为它解决了一个核心问题：

> 同群多个并行话题，怎么避免上下文串线。

如果你的群里会同时跑多个问题、多个 bot，`thread_isolation` 基本是应该优先考虑的配置。

---

## 第十二章：如果不开 thread isolation，它又是怎么分会话的

飞书平台的 session key 逻辑大致是三档：

### 1. 开 `thread_isolation`

按 thread / root 消息分会话。

### 2. 开 `share_session_in_channel`

整条群频道共享一个 session。

### 3. 两者都不开

按：

```text
feishu:<chatID>:<userID>
```

做“同群按用户分会话”。

这说明 cc-connect 在飞书群聊里不是只有一种会话策略，而是提供了三种粒度：

- 按 thread
- 按 channel
- 按 user

这也是它能在真实群聊里工作的原因之一。

---

## 第十三章：那多智能体在飞书群里的协作，实际是什么体验

如果把前面的设计组合起来，飞书群里的多智能体协作大概长这样：

### 场景 1：一个群里挂多个 project bot

例如：

- `claudecode`
- `codex`
- `gemini`

### 场景 2：在群里先绑定这些 bot

```text
/bind claudecode
/bind codex
/bind gemini
```

### 场景 3：人类在群里发问题

比如先 @Claude 让它分析问题。

### 场景 4：Claude 通过 relay 再问 Gemini 或 Codex

cc-connect 会把这次转发也显示到群里。

### 场景 5：Gemini / Codex 返回结果，结果继续回到群里

于是这个群的体验就会变成：

- 人可以看见 bot 之间怎么转任务
- bot 之间不是暗箱通信
- 每个 bot 仍然用自己的 project/workspace 在工作

所以它确实能在飞书群里协作，只是这种协作方式更像：

> **群聊里显式接力**

而不是：

> **后台全自动多 agent pipeline**

---

## 第十四章：`/bind setup` 说明它连 agent 提示词也考虑到了

文档里还有一个容易忽略但很关键的命令：

```text
/bind setup
```

这条命令的作用不是“绑定 project”，而是把 cc-connect 的系统提示写进某些 agent 的 memory 文件里。

原因很简单：

- 不是所有 agent 都原生支持把 cc-connect 的系统提示自动注入
- 而 relay、cron、附件回传这类能力，需要 agent 明白应该调用什么命令

所以 `/bind setup` 的本质是：

> **让 agent 学会如何在 cc-connect 生态里协作。**

这进一步说明 cc-connect 的编排不是“纯平台层”的，而是平台、会话、agent 指令三者一起工作的。

---

## 第十五章：它更适合什么样的编排任务

从当前实现看，cc-connect 特别适合下面几类编排：

### 1. 群聊中的问答接力

一个 bot 分析问题，另一个 bot 给不同角度意见。

### 2. 多项目视角协作

不同 project 绑定不同 workspace，让 bot 从不同代码库看同一个问题。

### 3. 不同 agent 特长互补

比如：

- Claude Code 偏执行与代码编辑
- Codex 偏终端式工程协作
- Gemini 偏另一套模型视角

### 4. 人在回路里的协作式编排

人类不是退出流程，而是始终能在群里看到、打断、继续推进。

这也是 cc-connect 和很多“自动 agent workflow”产品最不同的地方。

---

## 第十六章：它不太适合什么

反过来说，下面这些就不是它当前最强的方向：

### 1. 复杂 DAG 任务图执行

比如自动拆成十几个节点、按依赖并发跑、自动回收中间状态。

### 2. 无人值守的深度 agent pipeline

cc-connect 可以定时、可以 relay，但它的核心仍然是聊天驱动，而不是后台 job orchestration。

### 3. 完全自动的角色路由系统

它有多 bot relay，但默认不是“看任务内容自动选最优 bot”。

### 4. 强共享上下文的 agent swarm

每个 project / agent / workspace 还是分开的，cc-connect 不会把所有 bot 上下文融合成一个大脑。

所以如果你的预期是“全自动多 agent 平台”，那会有落差；但如果你的预期是“群聊里透明、稳定、可控的多 bot 协作”，它反而很合适。

---

## 第十七章：如果你要在飞书群里认真使用，建议这样配

如果只是从当前实现出发，我会给一个很务实的建议顺序：

### 1. 先从 `@机器人` 模式开始

不要一开始就开 `group_reply_all`。

### 2. 优先打开 `thread_isolation`

尤其是你准备在群里并行跑多个话题时。

### 3. 每个 bot 对应清晰的 project 名

因为 relay 的目标依赖精确 project name。

### 4. 先用 `/bind` 建立少量明确协作关系

不要一下子把所有 bot 都堆进一个群。

### 5. 对高权限 agent 保守配置 mode

因为 relay 路径里权限是自动放行的。

如果只总结成一句话，就是：

> **cc-connect 在飞书群里能工作，而且能做多 bot 协作，但最适合“透明、可控、显式”的协作，不适合“黑盒、全自动、重调度”的编排。**

---

## 第十八章：最后一句话总结

如果你问：

> cc-connect 在多智能体之间编排是什么形式？

最准确的回答是：

> **以 project 为单位，把多个 Agent 绑定到同一聊天场景，通过 `/bind` 和 `relay` 做显式消息转发，并让每个 Agent 保持独立 workspace 与独立 relay session 的群聊协作式编排。**

如果你再问：

> 能在飞书群里工作吗？

答案也是明确的：

> **能，而且飞书群聊是它比较成熟的一条使用路径；默认走 @提及触发，也支持 `group_reply_all`、`thread_isolation` 和多 bot 绑定。**
