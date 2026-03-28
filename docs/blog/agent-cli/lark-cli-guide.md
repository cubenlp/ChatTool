# Lark CLI 教程：认证、三层命令体系与 Agent 场景下的安全用法

这一篇讲官方的 **`lark-cli`**，仓库是 `larksuite/cli`。

它和 Codex、OpenCode、Claude Code 这类“通用代码 Agent CLI”不太一样：`lark-cli` 不是让模型自己去摸索网页或拼 SDK，而是把 **飞书/Lark 开放平台能力直接整理成命令行接口**，同时又专门给 AI Agent 准备了 Skills、结构化输出和更稳妥的默认参数。

本文内容基于 **2026-03-29** 查看官方仓库 `https://github.com/larksuite/cli` 及其 README 整理，重点讲“终端里怎么用”。

---

## 先理解它是什么

官方对 `lark-cli` 的定位很明确：

- 面向飞书 / Lark 开放平台
- 同时服务 **人类用户** 和 **AI Agent**
- 覆盖消息、文档、多维表格、日历、任务、邮箱、会议等业务域
- 命令设计分成三层：**快捷命令 → API 命令 → 原始 API 调用**

如果只记一句判断标准，可以记这个：

> **想在终端里稳定操作飞书开放平台，优先用 `lark-cli`；想自己再封装 SDK，只在它现成命令不够时再考虑。**

---

## 第一步：安装

官方推荐从 npm 安装：

```bash
npm install -g @larksuite/cli
```

然后再安装它配套的 Skills：

```bash
npx skills add larksuite/cli -y -g
```

如果你是从源码安装，README 给出的方式是：

```bash
git clone https://github.com/larksuite/cli.git
cd cli
make install

npx skills add larksuite/cli -y -g
```

### 环境要求

README 里提到的前提是：

- 日常使用至少要有 `Node.js`、`npm` / `npx`
- 只有从源码构建时才需要 `Go >= 1.23` 和 `Python 3`

---

## 第二步：先做配置和登录

`lark-cli` 的第一次使用，不是直接发消息，而是先完成两件事：

1. 配置应用凭证
2. 完成登录授权

### 初始化应用配置

```bash
lark-cli config init
```

如果你是在 Agent 场景下让用户配合完成浏览器授权，官方 README 还给了一个更适合自动化的入口：

```bash
lark-cli config init --new
```

这个模式会输出授权链接，用户在浏览器完成配置后，命令再自动退出。

### 登录授权

最常见的登录方式：

```bash
lark-cli auth login
```

推荐直接用常见权限集合：

```bash
lark-cli auth login --recommend
```

查看当前登录状态：

```bash
lark-cli auth status
```

列出当前 app 可申请的 scope：

```bash
lark-cli auth scopes
```

列出本地已经登录过的身份：

```bash
lark-cli auth list
```

---

## 登录时最实用的几种写法

如果你不想每次都走完整交互流程，README 里给了几种常用筛选方式。

### 按业务域申请权限

```bash
lark-cli auth login --domain calendar,task
```

适合你这次只想用日历和任务，不想一上来就申请一大堆能力。

### 精确申请某个 scope

```bash
lark-cli auth login --scope "calendar:calendar:readonly"
```

这类方式适合做最小权限控制，尤其适合自动化任务和内部受控环境。

### Agent 非阻塞登录

如果你是让 Agent 帮用户完成配置，最值得记住的是 `--no-wait`：

```bash
lark-cli auth login --domain calendar --no-wait
```

这个模式下，CLI 会尽快返回验证 URL，不会一直阻塞在终端里等用户操作。

之后可以带着设备码继续轮询：

```bash
lark-cli auth login --device-code <DEVICE_CODE>
```

这套流程很适合：

- 远程 SSH 环境
- 让 AI Agent 先发链接给用户
- 用户在浏览器完成授权后再回到终端继续

---

## 身份切换：区分 user 和 bot

`lark-cli` 一个很重要的设计是：**很多命令支持显式指定以用户还是机器人身份执行。**

例如：

```bash
lark-cli calendar +agenda --as user
lark-cli im +messages-send --as bot --chat-id "oc_xxx" --text "Hello"
```

这点非常关键，因为飞书很多 API 的可见性、权限和行为都跟当前身份有关。

如果你碰到“同一个命令有时能跑、有时拿不到数据”，先检查这三件事：

- 当前登录的是谁
- 当前 scope 是否够
- 当前是不是该用 `--as user` 或 `--as bot`

---

## 核心设计：三层命令体系

`lark-cli` 最值得学的，不是某一条具体命令，而是它把调用方式拆成了三层。

---

## 第一层：快捷命令 `+`，最适合日常使用

快捷命令是 README 里最推荐的人机通用入口，特点是：

- 参数更短
- 默认值更合理
- 输出更适合直接阅读
- 通常还支持 `--dry-run`

比如：

```bash
lark-cli calendar +agenda
lark-cli im +messages-send --chat-id "oc_xxx" --text "Hello"
lark-cli docs +create --title "Weekly Report" --markdown "# Progress\n- Completed feature X"
```

如果你的目标是“尽快把事做完”，一般先从快捷命令开始。

查看某个业务域有哪些快捷命令：

```bash
lark-cli <service> --help
```

例如：

```bash
lark-cli calendar --help
lark-cli im --help
lark-cli docs --help
```

---

## 第二层：API 命令，对应平台能力但还保留命令结构

当快捷命令不够细，或者你想更贴近官方 API 模型时，就用 API 命令。

README 里的例子：

```bash
lark-cli calendar calendars list
lark-cli calendar events instance_view --params '{"calendar_id":"primary","start_time":"1700000000","end_time":"1700086400"}'
```

这一层的特点是：

- 命令名通常更贴近官方端点语义
- 参数会更多、更显式
- 适合做精确控制
- 比直接发原始 HTTP 请求仍然更省心

如果你已经在读开放平台文档，这一层通常会比快捷命令更容易对上官方概念。

---

## 第三层：原始 API 调用，覆盖面最大

如果前两层都不够，`lark-cli` 还允许你直接调用开放平台接口。

```bash
lark-cli api GET /open-apis/calendar/v4/calendars
lark-cli api POST /open-apis/im/v1/messages --params '{"receive_id_type":"chat_id"}' --body '{"receive_id":"oc_xxx","msg_type":"text","content":"{\"text\":\"Hello\"}"}'
```

这一层适合：

- 官方已经支持，但快捷命令还没包好
- 你要验证某个具体接口行为
- 你希望 1:1 对照开放平台文档

你可以把三层理解成：

- **先用 `+` 命令做事**
- **不够细就切 API 命令**
- **再不够就直接 `api`**

---

## 常用输出格式：给人看，还是给程序吃

README 里给出的输出格式很实用：

```bash
--format json
--format pretty
--format table
--format ndjson
--format csv
```

可以粗略记成：

- `json`：默认，信息最全
- `pretty`：给人读更舒服
- `table`：列表数据更直观
- `ndjson`：适合管道和流式处理
- `csv`：适合导出给表格工具

如果你在 shell 里串后续处理，`json` 和 `ndjson` 最常用；如果你只是自己读，`pretty` 和 `table` 更轻松。

---

## 分页和批量拉取

飞书里很多列表接口都会分页，所以官方专门给了统一参数：

```bash
--page-all
--page-limit 5
--page-delay 500
```

例如：

```bash
lark-cli mail ... --page-all
```

这类参数很适合做“先小范围试，再全量拉”的节奏：

1. 先不加 `--page-all` 看单页结果
2. 确认字段没问题后再全量翻页
3. 需要限速时加 `--page-delay`

---

## 有副作用的命令，先 `--dry-run`

官方特别提了 `--dry-run`，这是很值得保留的习惯：

```bash
lark-cli im +messages-send --chat-id oc_xxx --text "hello" --dry-run
```

对发送消息、写文档、改任务、写表格这类操作，建议都先预演一次。尤其是把它接给 AI Agent 时，`--dry-run` 能显著降低误发和误写风险。

---

## `schema`：比翻文档更快的命令级自省

`lark-cli` 还有一个很适合边查边用的入口：

```bash
lark-cli schema
lark-cli schema calendar.events.instance_view
lark-cli schema im.messages.delete
```

它的价值是让你直接看到某个 API 方法对应的：

- 参数结构
- 请求体结构
- 响应结构
- 支持的身份
- 需要的 scopes

如果你经常在“README、开放平台文档、终端试命令”之间来回跳，`schema` 会是效率很高的中间层。

---

## 业务域覆盖很广，但建议先从 3 个方向上手

官方 README 列出的业务域很多：

- `calendar`
- `im`
- `docs`
- `drive`
- `base`
- `sheets`
- `task`
- `wiki`
- `contact`
- `mail`
- `meetings`

如果你第一次接触，建议优先从这三块开始：

### 1. 即时通讯 `im`

最容易看到结果，适合验证认证和权限是否正常。

```bash
lark-cli im +messages-send --chat-id "oc_xxx" --text "Hello from CLI"
```

### 2. 日历 `calendar`

适合查 agenda、忙闲和时间建议，常见自动化价值很高。

```bash
lark-cli calendar +agenda
```

### 3. 文档 `docs`

适合做周报、会议记录、Agent 生成内容落地。

```bash
lark-cli docs +create --title "Weekly Report" --markdown "# 本周进展"
```

---

## 对 AI Agent 来说，它真正有价值的点

从 README 看，`lark-cli` 不是“顺手兼容 Agent”，而是明显按 Agent 场景设计过。

最有代表性的几个点是：

- 提供配套 Skills，减少 Agent 自己拼 prompt 和 API 的成本
- 输出结构化，方便被脚本或其他 Agent 接住
- 命令命名和参数比原始接口更短、更稳定
- 有 `--no-wait`、`--device-code` 这类适合人机协作的认证流程
- 强调 `--dry-run` 和安全提示，降低误操作风险

所以它特别适合这类工作流：

1. Agent 帮用户完成安装和初始化
2. Agent 发授权链接给用户
3. 用户在浏览器完成授权
4. Agent 回到终端执行 `calendar`、`docs`、`im` 等业务命令
5. 必要时再切到底层 `api`

---

## 使用时要特别注意的风险点

官方 README 对安全提示写得很重，这不是形式化文案，而是真的要重视。

最核心的风险是：

- Agent 可能会幻觉、误解任务或过度执行
- 一旦授权，命令是在你的飞书身份与 scope 范围内执行
- 如果把机器人拉进群聊或暴露给其他人，可能造成权限滥用和数据泄露

比较稳妥的实践是：

- 初次接入时只申请最小 scope
- 有副作用操作默认先 `--dry-run`
- 明确区分 `--as user` 和 `--as bot`
- 先在私人环境、小数据范围内验证
- 不主动关闭它默认的安全保护

---

## 一条实用上手路线

如果你只是想今天把它跑起来，可以按这个顺序：

```bash
npm install -g @larksuite/cli
npx skills add larksuite/cli -y -g
lark-cli config init
lark-cli auth login --recommend
lark-cli auth status
lark-cli calendar +agenda
```

如果你是要把它交给 Agent 使用，更推荐下面这条：

```bash
npm install -g @larksuite/cli
npx skills add larksuite/cli -y -g
lark-cli config init --new
lark-cli auth login --recommend --no-wait
lark-cli auth status
```

之后再根据实际任务进入：

- `im`：发消息、查消息、处理附件
- `docs`：写文档、生成周报、沉淀知识
- `calendar`：看日程、查忙闲、辅助排会
- `task`：创建和跟踪待办

---

## 最后怎么选

如果你平时主要在飞书开放平台上做自动化，`lark-cli` 最大的价值不是“命令多”，而是它把使用路线整理得很清楚：

- **先完成配置和登录**
- **先用快捷命令解决 80% 的问题**
- **需要精细控制时再切 API 命令**
- **最后才使用原始 API**

对于人类开发者，这是一个更省事的飞书终端工具；对于 AI Agent，这是一个比“直接调 SDK + 自己拼 OAuth 流程”稳定得多的执行层。
