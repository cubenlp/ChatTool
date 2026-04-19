# 从 auto-loop 学 ChatLoop：如何把“能继续跑”做成真正可用的 PRD loop

这篇文章记录一次很具体的工程回顾：

- 我们为什么一开始做出来的 `chatloop` 不够用
- `opencode-auto-loop` 到底解决了什么问题
- 我们最后决定学它什么、不学它什么
- 一个 PRD-aware loop 至少要满足哪些产品条件，才不至于沦为“提示词套娃”

如果只用一句话概括这次结论，那就是：

> 不要重新发明一套看起来像 loop 的 prompt。先学会 `auto-loop` 为什么能让模型继续跑，再把 `PRD.md` 这层约束嫁接上去。

---

## 一、问题是怎么暴露出来的

`chatloop` 一开始的目标很明确：

- 用户在 project 中写好 `PRD.md`
- 显式执行 `/chatloop ...`
- 插件在模型停下后继续推进
- 每轮都重新围绕 `PRD.md` 理解任务

听起来没问题，但实际调试很快暴露出两个硬伤：

1. **首轮不够硬**
2. **continuation 不够强**

最典型的问题是：

```text
/chatloop 调研 ralph loop
```

如果首轮只是把这句话原样转发给模型，那么：

- `PRD.md` 根本没有被强制带进去
- `memory.md` / `progress.md` 没有被明确要求重读
- 完成规则也只是隐含存在

这意味着看起来像“PRD loop”，实际上只是：

- 先发了一句普通 prompt
- 然后期待后面的 idle continuation 替你兜底

这在产品上不成立。

因为用户真正想要的是：

- **一开始就强制进入受控模式**
- 而不是“也许后面会变成 loop”

---

## 二、为什么 auto-loop 更像一个“真 loop”

`opencode-auto-loop` 的价值，不在于它写了多少 prompt 文案，而在于它有一套完整的 continuation 状态机。

从代码看，它做了这几件关键事：

### 1. 启动时先写 state

它会在 `.opencode/auto-loop.local.md` 里保存：

- active
- iteration
- maxIterations
- sessionId
- 原始任务 prompt
- 已完成项 / 下一步项

这不是“提示词记忆”，而是插件自己的持久状态。

### 2. 每次 idle 都判断“要不要继续”

它不是简单地“AI 停了再说”，而是每次都检查：

- state 是否 active
- session 是否匹配
- debounce 是否通过
- session 是否真的 idle
- 最近 assistant 消息是否已经完成

只要条件不满足完成，它就继续发下一轮 prompt。

### 3. completion gate 不是纯口头约定

`auto-loop` 不会因为 assistant 随便吐一个 done 就结束。

它会看：

- 有没有 `STATUS: COMPLETE`
- 有没有 `STATUS: IN_PROGRESS`
- `## Next Steps` 里是不是还留着 `- [ ]`

如果 completion signal 不合法，它会拒绝结束，并继续跑。

这是它最值得学的地方：

> loop 的价值不只是“继续发 prompt”，而是“决定什么时候不允许停”。

### 4. 它对用户有明确反馈

`auto-loop` 还做了一件看起来小、但实际上非常重要的事：

- 启动时弹 toast
- 每次迭代弹 toast
- 被拒绝完成时弹 toast
- 遇到错误暂停时弹 toast
- 到最大轮数时弹 toast

这解决了一个很实际的问题：

> 用户不能只靠猜，必须能看见 loop 当前是不是 active、正在第几轮、为什么停了。

---

## 三、不能乱写一套 prompt

这次最重要的收敛点，是我们不再单独设计一套“看起来也合理”的 `chatloop` prompt。

原因很简单：

- `auto-loop` 的 prompt 骨架已经被它自己的状态机验证过
- 它的结构和 gate 是配套的
- 如果另起一套 prompt，很容易再次滑回“提示词看起来很强，实际没有状态机支持”

所以最终最稳的做法是：

### 直接借它的骨架

也就是 continuation prompt 永远保留这些部分：

- `Original task`
- `Completed`
- `Next Steps`
- 继续工作的规则
- completion rules

然后 **只补 ChatLoop 特有的 PRD 头部**：

- `Project path`
- `Required entry file: .../PRD.md`
- `Read PRD.md from scratch before doing anything else`
- `If memory.md or progress.md exist...`

一句话：

> 先借 `auto-loop` 解决“怎么继续跑”，再让 `chatloop` 负责“围绕什么继续跑”。

---

## 四、ChatLoop 最后学了 auto-loop 哪些东西

这轮改造后，`chatloop` 主要学了四类东西。

### 1. 启动首轮也必须强约束

现在 `/chatloop <message>` 不再原样转发用户消息。

首轮会直接生成 bootstrap prompt，其中固定包含：

- `Project path`
- `Required entry file: .../PRD.md`
- `Original task`
- `## Completed`
- `## Next Steps`
- `STATUS: IN_PROGRESS / STATUS: COMPLETE`
- completion gate 规则

这一步其实很关键，因为它把 loop 的约束前移到了第一轮，而不是等 idle 之后再补救。

### 2. 引入结构化 progress

现在 `chatloop` 也会把 assistant 输出里的：

- `## Completed`
- `## Next Steps`

提取出来，写回 `.opencode/chatloop.local.md`，下一轮再带回 continuation prompt。

这样 continuation 就不只是“继续做”，而是“继续当前还没完成的部分”。

### 3. 引入更强 completion gate

现在 `chatloop` 不再只看：

- `<complete>DONE</complete>`

它还要求：

- `STATUS: COMPLETE`
- `Next Steps` 没有未完成的 `- [ ]`

否则会：

- 记录 `chatloop.complete.rejected`
- 拒绝结束
- 继续 loop

### 4. 引入 toast 风格反馈

这部分是直接向 `auto-loop` 学的体验层能力。

现在 `chatloop` 会在这些阶段给 toast：

- 启动成功
- 已经 active 又重复启动
- 继续到下一轮
- completion 被拒绝
- 正常完成
- session error 暂停
- 到最大轮数停止
- session compact 后恢复上下文

这能明显降低“感觉像没生效”的调试成本。

---

## 五、还有什么是 auto-loop 有、但 chatloop 还没完全吃透的

虽然这轮已经明显往前走了一大步，但还有几个现实边界要说清楚。

### 1. 它仍然不是“硬清空上下文”

不管是 `auto-loop` 还是现在的 `chatloop`，本质上都还是：

- 同一个 session
- 每次 idle 后 `promptAsync`

它们更像：

- **强 continuation**

而不是：

- **硬 fresh session reset**

所以如果产品目标是“每轮都像新建会话一样完全无上下文”，那还得继续研究 OpenCode 的 session create / fork / delete / abort API，不能只靠 prompt 解决。

### 2. `opencode run` 不是验证 continuation 的理想方式

这轮真实验证里还有一个非常重要的发现：

- `opencode run` 在首轮 assistant 停下并发布 `session.idle` 后，会立即 dispose instance

这意味着：

- 用 `run` 可以验证首轮 bootstrap prompt 是否强制注入了 `PRD` 约束
- 但不适合验证“后续 continuation / maxIterations 是否真的继续跑”

因为 run 模式自己先结束了。

真正要验证 continuation，应该放到：

- TUI
- 或 attach 到长生命周期 session

### 3. 安装链路要避免插件双加载

调试过程中还发现过一个很典型的坑：

- `opencode.json` 同时保留旧的 `file://.../plugins/chatloop/index.ts`
- 和新的 `file://.../plugins/chatloop`

这样会让插件双加载，表现为：

- 每条事件日志都写两次
- continuation 行为变得很难判断

所以安装阶段必须自动清掉 legacy entry。

---

## 六、这次最大的收获

这次最大的收获其实不是“写了一个更长的 prompt”，而是把 loop 的边界想清楚了。

一个真的有用的 loop，至少要同时满足：

1. **首轮就进入受控模式**
2. **停下来以后会继续跑**
3. **不能随便提前结束**
4. **用户能看见它当前处于什么状态**

而 `auto-loop` 的价值就在于，它已经把第 2、3、4 条做得比较完整。

`chatloop` 真正要做的，不是另写一套“更像 PRD”的文案，而是：

- 站在 `auto-loop` 的 continuation 状态机上
- 把 `PRD.md` 变成它的任务主入口

换句话说：

> `chatloop` 不应该是一个“新的 loop 发明”，而应该是一个 **PRD-aware auto-loop**。

---

## 七、后续最值得继续验证的点

如果继续推进，最有价值的验证顺序应该是：

1. 在 OpenCode TUI 中验证真实 continuation 是否会稳定触发
2. 看 `maxIterations` 在长生命周期 session 里是否真正生效
3. 验证 completion reject / accept 是否符合预期
4. 再决定是否值得继续研究“每轮新 session”的更硬控制方案

在这之前，再去写另一套 loop prompt，意义已经不大了。

因为这次最明确的教训就是：

> 你要学会别人，才能做好自己。
