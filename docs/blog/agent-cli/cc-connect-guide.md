# cc-connect 教程：由浅到深，把本地 Agent 接进飞书、Telegram 和 Slack

这一篇不讲某一个 Agent CLI，而讲 **cc-connect**。

如果说 Codex、Claude Code、OpenCode 解决的是“你怎么在终端里和 Agent 协作”，那 cc-connect 解决的是另一件事：

> **怎么把这些本地 Agent 接到飞书、Telegram、Slack 这类聊天平台里，让它们脱离终端继续可用。**

本文内容基于本机在 **2026-03-27** 执行 `cc-connect --help`、`cc-connect send --help`、`cc-connect cron add --help` 和 `cc-connect config-example` 的结果整理。写法按“由浅到深”展开，所有内容都放在这一篇里。

---

## 第一章：先把它看成什么

`cc-connect --help` 的开头其实已经把定位说透了：

> Bridge your messaging platforms to local AI coding agents.

它支持的 Agent 有：

- Claude Code
- Codex
- Cursor
- Gemini CLI
- Qoder CLI
- OpenCode

它支持的平台有：

- Feishu
- Telegram
- Slack
- DingTalk
- Discord
- LINE
- WeChat Work
- QQ
- QQ Bot

所以它不是模型本身，也不是另一个 IDE Agent。更准确地说，它是一个 **桥接层**：

- 一端连本地 Agent CLI
- 一端连消息平台
- 中间负责消息转发、会话保持、权限确认、定时任务和多项目管理

如果只用一句话理解：

> **cc-connect 是把“终端里的 Agent”变成“聊天软件里也能继续工作的 Agent”。**

---

## 第二章：为什么你会需要它

如果你始终坐在电脑前，直接用 `codex`、`claude`、`opencode` 往往已经够了。

但一旦出现下面这些需求，cc-connect 就会开始变得有价值：

- 想在手机里继续和本地 Agent 对话
- 想把某个项目的 Agent 挂到飞书群或 Telegram
- 想让 Agent 在聊天里申请权限，而不是只在终端里等你
- 想让 Agent 定时汇报
- 想同时管理多个项目、多个 Agent、多个平台

也就是说，cc-connect 不主要解决“模型能力不够”的问题，它主要解决的是：

**Agent 已经有了，怎么让它更容易被持续使用。**

---

## 第三章：先读懂 `--help`，别急着配

先看顶层帮助，你会发现命令其实可以分成四组。

### 1. 主进程入口

```bash
cc-connect
cc-connect --config /path/to/config.toml
```

这组命令负责启动 cc-connect 本体。

### 2. 后台服务管理

```bash
cc-connect daemon install
cc-connect daemon start
cc-connect daemon stop
cc-connect daemon restart
cc-connect daemon status
cc-connect daemon logs -f
```

这组命令负责把 cc-connect 变成长期常驻服务。

### 3. 运行中的操作命令

```bash
cc-connect send
cc-connect cron
cc-connect relay
cc-connect provider
```

这是最值得深入理解的一组，因为它们定义了“启动以后你还能做什么”。

### 4. 运维和辅助命令

```bash
cc-connect update
cc-connect check-update
cc-connect config-example
```

其中最重要的是：

```bash
cc-connect config-example
```

因为它会直接打印完整的注释配置模板。

---

## 第四章：最核心的配置思路，其实不是机器人，而是 project

`config-example` 里有一句最关键的话：

> Each `[[projects]]` entry binds one code directory to its own agent + platforms.

这句话非常重要。它说明 cc-connect 的最小配置单位不是“一个账号”或“一个机器人”，而是 **一个 project**。

一个 project 通常会绑定：

- 一个代码目录
- 一个 Agent 类型
- 一个或多个消息平台

这意味着 cc-connect 更像“多项目 Agent 编排层”，而不是简单的聊天转发脚本。

默认配置路径是：

- 当前目录 `./config.toml`
- 或 `~/.cc-connect/config.toml`

你也可以显式指定：

```bash
cc-connect --config /path/to/config.toml
```

---

## 第五章：先只跑通一个最小项目

第一次上手，不要一开始就配三个项目、两个平台、五种 Provider。先跑通一个最小例子。

例如一个最简单的“Claude Code + 飞书”配置可以写成：

```toml
[[projects]]
name = "my-backend"

[projects.agent]
type = "claudecode"

[projects.agent.options]
work_dir = "/path/to/backend"
mode = "default"

[[projects.platforms]]
type = "feishu"

[projects.platforms.options]
app_id = "your-feishu-app-id"
app_secret = "your-feishu-app-secret"
```

这里只需要先理解五个字段：

- `name`：项目名
- `type`：Agent 类型
- `work_dir`：Agent 处理任务时实际工作的目录
- `mode`：执行/审批模式
- `platforms`：这个项目接入的平台

等这一条链路跑通之后，再去扩展其他能力。

---

## 第六章：不同 Agent，用不同 `type`

从 `config-example` 可以看到，cc-connect 已经内置了多种 Agent 类型。

例如：

- `type = "claudecode"`
- `type = "codex"`
- `type = "opencode"`
- `type = "gemini"`
- `type = "cursor"`
- `type = "qoder"`

这不是小细节，而是它的核心设计之一。

因为 cc-connect 并不是强行把所有 Agent 包装成一个抽象接口，而是允许你按项目选择最合适的后端。

例如你完全可以这样拆：

- 后端项目：Claude Code
- 文档项目：Codex
- 试验项目：OpenCode

这几个项目可以一起挂在同一个 cc-connect 进程里。

---

## 第七章：`mode` 才是真正决定体验的开关

很多人第一次配置时只盯着 `app_id`、`api_key` 这种字段，但真正决定使用体验的，经常是 `mode`。

在 `config-example` 里，不同 Agent 的 mode 取值并不一样。

Claude Code 的示例：

```toml
mode = "default" # "default" | "acceptEdits" | "plan" | "bypassPermissions"
```

Codex 的示例：

```toml
mode = "suggest"  # "suggest" | "auto-edit" | "full-auto" | "yolo"
```

OpenCode 的示例：

```toml
mode = "default"  # "default" | "yolo"
```

这说明 cc-connect 没有简单粗暴地统一所有 Agent 的权限模型，而是尽量保留它们原本的行为方式。

所以配置时你应该先问自己：

- 这个项目是偏保守还是偏自动
- 这个项目是在私聊里用，还是在群聊里用
- 这个项目是否允许更激进的自动执行

如果这一步没想清楚，后面即使“能跑”，实际体验也常常会很差。

---

## 第八章：平台配置不是附属品，而是 project 的另一半

一个 project 不只是“Agent 怎么跑”，还包括“消息从哪来”。

平台配置一般长这样：

```toml
[[projects.platforms]]
type = "feishu"

[projects.platforms.options]
app_id = "..."
app_secret = "..."
```

样例里还给了这些平台的配置模板：

- Feishu
- DingTalk
- Telegram
- Slack
- Discord
- LINE
- WeCom
- QQ
- QQ Bot

第一次上手时，建议先选一个最简单的平台跑通。通常优先是：

- 飞书
- Telegram

原因很简单：路径比较直接，排障成本也更低。

---

## 第九章：最基础的使用方式，就是先把主进程跑起来

配置写好后，最简单的启动方式就是：

```bash
cc-connect
```

或者：

```bash
cc-connect --config ./config.toml
```

这里建议按这个顺序来：

1. 先前台运行
2. 去平台里发一条消息测试
3. 确认 Agent 能收到并回复
4. 确认权限和执行流程符合预期
5. 最后再考虑 daemon 化

不要一开始就上后台服务，否则排查配置问题会更慢。

---

## 第十章：`daemon` 是“用起来”和“挂起来”的分界线

当前台跑通后，下一步通常就是 `daemon`。

安装并启动：

```bash
cc-connect daemon install
```

常用维护命令：

```bash
cc-connect daemon status
cc-connect daemon logs -f
cc-connect daemon restart
cc-connect daemon stop
cc-connect daemon uninstall
```

这组命令的意义不是“更高级”，而是让 cc-connect 从一个你手工运行的程序，变成一个长期常驻的后台服务。

如果你的目标是：

- 家里开发机长期在线
- 服务器上持续挂机器人
- 手机里随时都能找到项目 Agent

那 `daemon` 基本是必走的一步。

---

## 第十一章：`send` 是最容易低估的命令

很多人看到 cc-connect，会以为它只能“被动接收聊天平台消息”。其实不是。

`send` 允许你从本地 CLI 主动往一个活跃会话推消息。

最简单的形式：

```bash
cc-connect send "Daily summary: ..."
```

更稳妥的形式是指定项目：

```bash
cc-connect send -p my-backend -m "Build completed successfully"
```

长文本建议走 stdin：

```bash
cc-connect send -p my-backend --stdin <<'EOF'
请根据今天的提交记录生成一段日报。
重点说明：
1. 改了哪些模块
2. 还有哪些风险
EOF
```

`send` 真正有价值的地方在于：

- 脚本可以主动把结果推给 Agent 会话
- 你可以在终端里补充一条任务，不用切回聊天软件
- 某些自动化流程可以把上下文继续塞进现有对话

它让 cc-connect 从“消息桥”进一步变成“工作流入口”。

---

## 第十二章：`cron` 让 Agent 从响应式变成主动式

`cron` 是 cc-connect 里非常值得用的一组命令。

新增任务：

```bash
cc-connect cron add --project my-backend --cron "0 6 * * *" --prompt "Collect GitHub trending data" --desc "Daily Trending"
```

也支持位置参数形式：

```bash
cc-connect cron add 0 6 * * * Collect GitHub trending data and send me a summary
```

查看任务：

```bash
cc-connect cron list
```

删除任务：

```bash
cc-connect cron del <ID>
```

这组命令的重要性在于，它让 Agent 不再只是“你问一句，它答一句”，而是可以定时主动执行轻任务，比如：

- 每天晨报
- 每周项目总结
- 定期检查某个仓库状态
- 定时收集外部信息后汇总

一旦配上 `daemon`，这类用法就会很自然。

---

## 第十三章：`provider` 解决的是项目级模型源切换

cc-connect 还提供了 provider 管理能力：

```bash
cc-connect provider list --project my-backend
cc-connect provider add --project my-backend --name relay --api-key sk-xxx
cc-connect provider remove --project my-backend --name relay
```

从 `config-example` 看，provider 是 `projects.agent` 下的一个可选层。

它适合这些场景：

- 同一个项目要切不同 API key
- 你在 Claude Code 外面接了 router / relay
- 不同项目希望绑定不同计费来源

这类能力不一定是第一天就要用，但一旦进入多项目、多 Provider 管理阶段，它会非常实用。

---

## 第十四章：`relay` 说明它不只支持单项目单会话

`--help` 里还有一组容易被忽略的命令：

```bash
cc-connect relay send
```

帮助对它的描述是：

> Cross-project message relay

这意味着 cc-connect 的设计并不局限于“每个平台只连一个项目”。它已经考虑到了**项目之间转消息**的需求。

这类能力适合更复杂的编排，比如：

- 一个项目生成结果，另一个项目继续处理
- 一个 Agent 负责写代码，另一个 Agent 负责审查
- 在不同工作目录、不同 Agent 之间转交任务

这已经不是入门层能力了，但它说明 cc-connect 的目标从来不只是“把聊天接起来”，而是想做一层真正的 Agent 工作流连接器。

---

## 第十五章：`config-example` 不是参考资料，而是起点

如果你第一次配 cc-connect，不建议从空白文件开始写。

直接先看完整模板：

```bash
cc-connect config-example
```

更实用的做法是直接导出：

```bash
cc-connect config-example > config.toml
```

然后删掉不用的部分，再逐项填写。

这是当前 CLI 自己提供的带注释模板，通常会比别人博客里的截图更可靠。

---

## 第十六章：推荐的上手顺序

如果你想少走弯路，可以按这个顺序来：

1. 先看 `cc-connect --help`，只理解它是桥接层
2. 再看 `cc-connect config-example`，理解 project 结构
3. 先只配一个 project、一个 Agent、一个平台
4. 前台启动 `cc-connect`
5. 在平台里发消息验证
6. 再切到 `daemon`
7. 再加 `send`
8. 最后再碰 `cron`、`provider`、`relay`

这套顺序的关键点在于：

> **先把一条链路跑通，再逐步叠加能力。**

---

## 第十七章：什么时候该用 cc-connect

如果你只是坐在终端前自己用 Agent，cc-connect 往往不是第一优先级。

但如果你已经有下面这些需求，它就很值得上：

- 想在手机里和本地 Agent 继续对话
- 想把多个项目接到不同 IM 平台
- 想把权限确认搬到聊天界面里做
- 想让 Agent 定时主动汇报
- 想让本地 Agent 常驻在线

从这个角度看，cc-connect 不是替代 Codex、Claude、OpenCode，而是在它们外面补上一层：

- 消息入口
- 常驻运行
- 会话调度
- 定时任务
- 多项目桥接

这也是为什么它值得单独成一篇，而不是只在某个 Agent CLI 教程里顺手带一句。
