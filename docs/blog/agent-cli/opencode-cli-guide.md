# OpenCode CLI 教程：TUI、run、attach 与 session 的基本用法

这一篇讲 **OpenCode**。

如果说 Codex 的命令设计更接近“一个主命令 + 几个明确子任务入口”，那 OpenCode 的感觉更像是：**默认先进 TUI，需要单次执行时再切到 `run`，需要远程接入时再走 `serve/web/attach`。**

本文内容基于本机在 **2026-03-27** 执行 `opencode --help`、`opencode run --help`、`opencode session --help`、`opencode providers --help`、`opencode completion --help`、`opencode agent --help`、`opencode serve --help`、`opencode web --help`、`opencode attach --help`、`opencode models --help` 的结果整理，重点还是“怎么用”。

---

## 先理解 OpenCode 的入口结构

从总帮助看，OpenCode 的几个核心入口是：

- `opencode [project]`
- `opencode run [message..]`
- `opencode attach <url>`
- `opencode serve`
- `opencode web`
- `opencode session`
- `opencode providers`

其中最关键的判断可以先记成一句：

> **想进入本地交互界面，用 `opencode`；想一次发一条明确任务，用 `opencode run`；想连到已经跑起来的实例，用 `opencode attach`。**

---

## 第一步：先配置 provider

OpenCode 把模型供应商管理集中在 `providers` 下。

查看当前 provider 和凭据情况：

```bash
opencode providers list
```

登录某个 provider：

```bash
opencode providers login
```

或者带一个 URL：

```bash
opencode providers login <url>
```

登出：

```bash
opencode providers logout
```

如果你只是先确认当前环境有没有配好，通常先跑一遍 `opencode providers list` 就够了。

---

## 交互式入口：`opencode [project]`

OpenCode 顶层默认命令就是启动 TUI。

直接在当前目录打开：

```bash
opencode
```

指定项目目录启动：

```bash
opencode /path/to/project
```

这里的设计和 Codex 很不一样。Codex 顶层更像“进入一个 agent 会话”；OpenCode 顶层则更强调**直接启动自己的交互界面**。

### 顶层常用参数

指定模型：

```bash
opencode -m openai/gpt-5
```

继续上一次会话：

```bash
opencode --continue
```

按 session id 继续：

```bash
opencode --session <SESSION_ID>
```

从已有会话分叉：

```bash
opencode --continue --fork
```

进入时附带初始 prompt：

```bash
opencode --prompt "先阅读这个仓库，再总结入口文件"
```

指定 agent：

```bash
opencode --agent <AGENT_NAME>
```

这些参数说明 OpenCode 的会话续跑能力直接挂在顶层，不需要像 Codex 那样单独走 `resume`。

---

## 一次性命令入口：`opencode run`

如果你不想先进 TUI，而是希望直接发一条任务并拿结果，使用 `run`：

```bash
opencode run "总结当前目录的主要模块"
```

这是 OpenCode 里最接近 Codex `exec` 的入口。

### 继续已有会话后再发消息

```bash
opencode run --continue "继续刚才的分析"
```

或指定某个 session：

```bash
opencode run --session <SESSION_ID> "补充测试建议"
```

### Fork 后再运行

```bash
opencode run --continue --fork "换一种实现方案再试一次"
```

### 附带文件

```bash
opencode run -f ./error.png -f ./trace.log "根据附件定位问题"
```

### 指定格式输出

```bash
opencode run --format json "输出当前分析过程"
```

### 指定命令

```bash
opencode run --command "pytest -q" "先执行测试，再解释失败原因"
```

### 指定模型、变体、思考展示

```bash
opencode run -m openai/gpt-5 --variant high --thinking "审查这个改动的风险"
```

`run` 这一组参数说明 OpenCode 比较强调“围绕一次消息执行一组附加控制项”，尤其是文件附件、输出格式、模型变体这些。

---

## 会话管理：顶层能续跑，`session` 负责清理

OpenCode 的 session 管理分成两层：

- 继续会话：直接在顶层或 `run` 里用 `--continue` / `--session`
- 管理会话列表：用 `opencode session`

列出历史会话：

```bash
opencode session list
```

删除某个会话：

```bash
opencode session delete <SESSION_ID>
```

这个设计挺直接：**工作流参数放在工作命令上，维护动作放在 `session` 子命令里。**

---

## 本地服务、Web 和远程接入

OpenCode 不只是本地 TUI，它还提供了 server 形态。

### 启动 headless server

```bash
opencode serve
```

指定监听地址和端口：

```bash
opencode serve --hostname 127.0.0.1 --port 4096
```

### 启动服务并打开 Web 界面

```bash
opencode web
```

### 连接到正在运行的实例

```bash
opencode attach http://localhost:4096
```

连接远端实例时，也可以继续某个会话：

```bash
opencode attach http://localhost:4096 --continue
```

或者指定远端目录与密码：

```bash
opencode attach http://localhost:4096 --dir /workspace/demo --password <PASSWORD>
```

如果你的使用方式不只是“本机终端里开一个 Agent”，而是希望把 OpenCode 常驻成服务，再从别处接入，这一组命令就是重点。

---

## 模型、Agent 与补全

除了主流程，OpenCode 还把几个辅助能力拆得很明确。

### 列出模型

```bash
opencode models
```

只看某个 provider：

```bash
opencode models openai
```

需要更详细的元数据时：

```bash
opencode models --verbose
```

刷新模型缓存：

```bash
opencode models --refresh
```

### 管理 agent

```bash
opencode agent list
opencode agent create
```

### Shell 补全

```bash
opencode completion >> ~/.bashrc
```

这里有个值得单独记住的细节：**`opencode completion --help` 实际打印的是补全脚本本身，而不是简短帮助。**

这说明它的使用习惯更偏“把脚本直接重定向进 shell 配置文件”。

---

## 几个实用命令模板

可以先从下面几条开始。

### 1. 在当前项目直接进入 TUI

```bash
opencode .
```

### 2. 直接发起一次任务

```bash
opencode run "总结 src/ 下各目录职责"
```

### 3. 带文件做一次分析

```bash
opencode run -f ./screenshot.png "根据截图判断哪里出错了"
```

### 4. 接着上一次会话继续

```bash
opencode --continue
```

### 5. 启一个服务后再从别处接入

```bash
opencode serve --port 4096
opencode attach http://localhost:4096
```

---

## 怎么选入口

如果只按日常终端使用来分，OpenCode 的选择可以很简单：

- 想要完整交互界面：`opencode`
- 想快速发一条任务：`opencode run`
- 想继续历史会话：`opencode --continue` 或 `opencode run --continue`
- 想常驻成服务：`opencode serve` 或 `opencode web`
- 想连到已经启动的实例：`opencode attach`

OpenCode 的特点不是命令少，而是它把“本地界面”“一次性消息”“服务化接入”三件事拆得比较明显。

---

## 结语

从命令结构看，OpenCode 更像一个带会话能力的本地工作台：

- 默认就是进 TUI
- `run` 负责快速发任务
- `attach` 负责连接现成实例
- `serve/web` 负责把它变成服务

所以如果你的习惯是“先打开一个工作台，再在里面持续推进任务”，OpenCode 的入口会很顺；如果你更偏 shell 自动化，一般会更常用 `opencode run`。

下一篇再写 **Claude** 的命令行交互方式，最后把 Codex / OpenCode / Claude 三者放到同一套工作流里对比。
