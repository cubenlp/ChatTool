# 飞书 CLI 教程：官方 SDK 与文档探索，给 Agent 交互如虎添翼

如果要给 Agent 接飞书，我现在更推荐一条很务实的路线：

- 底层能力尽量站在官方 SDK 这一边
- 命令入口尽量复用官方 `lark-cli`
- ChatTool 只保留 setup 和最短调试链路

这样做的好处不是“看起来更官方”，而是**真的更省心**。

对于 Agent 开发，最麻烦的通常不是“发一个 HTTP 请求”，而是下面这些事：

- token 和身份边界怎么处理
- 哪些 API 该走 bot，哪些该走 user
- 文档、评论、权限、知识库是不是同一套 token
- 出错时怎么快速定位参数和 scope

官方 SDK 和官方 CLI 正好把这些麻烦收掉了很大一部分。

这篇文章偏教程，不追求穷举功能，而是回答两个更实际的问题：

1. 为什么官方飞书 CLI / SDK 很适合拿来做 Agent 的飞书交互
2. 如果从文档能力入手，最值得先实践哪一条链路

---

## 为什么说官方 SDK 很实用

很多时候我们说“用飞书 CLI”，本质上其实是在享受官方 SDK 带来的便利。

对 Agent 开发来说，这种便利主要体现在四个方面。

### 1. 命令面已经按领域分好

飞书里最容易让人混乱的一点是：文档相关能力并不是一个大命令就包完了。

官方 CLI 已经替你把领域拆好了：

- `docs`
  - 正文创建、读取、更新、搜索
- `drive`
  - 评论、回复、权限、文件侧动作
- `wiki`
  - 知识库节点解析
- `base`
  - 多维表格

这对 Agent 很友好，因为它天然鼓励你把任务拆成：

- 正文处理
- 评论处理
- 权限处理
- 知识库解析

而不是写一个“超级飞书工具”把所有事情糊在一起。

### 2. schema 和 help 很适合边探索边开发

如果你是手写 REST 调用，开发时最痛苦的是反复翻文档查：

- 参数名到底是什么
- `openid` 还是 `userid`
- query 参数和 body 参数谁放哪里

官方 CLI 可以直接在本地查：

```bash
lark-cli schema drive.permission.members.create
lark-cli drive permission.members create --help
```

这对 Agent 尤其重要，因为它意味着：

- 不用靠记忆猜 API
- 可以按 schema 构造最小请求
- 出错时能快速回到真实命令面校验

### 3. `--dry-run` 很适合有副作用的操作

做 Agent 自动化，真正危险的不是读，而是写。

比如加权限、回评论、更新正文时，最怕的是：

- token 错了
- 目标类型错了
- 参数位置错了

这时候官方 CLI 的 `--dry-run` 很好用：

```bash
lark-cli drive permission.members create --dry-run ...
```

它能先把实际要发的请求打印出来，再决定要不要真正执行。

这对 Agent 的价值非常直接：

- 降低误操作
- 便于排查
- 便于把“计划执行”和“真正执行”拆开

### 4. bot / user 边界更容易被看见

飞书自动化最容易被忽略的一件事是：

> 已经拿到 app_id / app_secret，不等于所有动作都能走 bot。

这次实践里很典型的一个边界就是：

```bash
lark-cli auth status
```

如果返回 bot-only，就意味着：

- 已知文档后的操作，很多还能走
- 但搜索和发现这类动作，可能就不行

比如：

```bash
lark-cli docs +search --as bot ...
```

在真实使用里会被直接拒绝，所以更适合视为 user 路线。

这种边界如果你是直接写 SDK 代码，很容易在业务逻辑里糊掉。  
而用了 CLI，你会更早地把它显式建模出来。

---

## ChatTool 在这里扮演什么角色

如果已经在 ChatTool 里维护飞书配置，最省事的入口不是手工装，而是：

```bash
chattool setup lark-cli
```

这条命令的价值不在于“帮你安装个 npm 包”，而在于它把开发过程里最烦的迁移工作做掉了：

- 检查 Node.js / npm
- 安装官方 `@larksuite/cli`
- 复用当前生效的 Feishu 配置

默认配置位置：

```text
~/.lark-cli/config.json
```

ChatTool 默认 Feishu 配置位置：

```text
~/.config/chattool/envs/Feishu/.env
```

也就是说，如果你原来就已经把飞书配置放在 ChatTool 里，切到官方 CLI 基本不需要再重输一遍。

而 ChatTool 自己保留的：

- `chattool lark info`
- `chattool lark send`
- `chattool lark chat`

更像是“最短调试入口”，不是再维护一套完整飞书产品面。

---

## 为什么文档能力特别适合拿来做 Agent 入口

如果你要给 Agent 接飞书，我认为最值得先下手的不是日历，也不是复杂审批，而是文档。

因为文档天然就是 Agent 工作流的落点：

- 计划可以写进文档
- 进度可以追加到文档
- review 可以挂在评论线程里
- 权限可以控制谁看、谁管
- 最后还能把链接发给群

也就是说，文档这条链天然就是：

```text
生成内容 -> 协作讨论 -> 授权 -> 送达
```

对于 Agent 交互，这条链的性价比非常高。

---

## 一条最值得先跑通的文档链路

如果只做最小实践，我建议先打通这一条：

```text
create -> fetch -> update -> comment -> reply -> permission -> send link
```

下面按教程方式过一遍。

### 第一步：创建文档

```bash
lark-cli docs +create \
  --as bot \
  --title "ChatTool Lark CLI Practice" \
  --markdown "$MARKDOWN"
```

这一步的意义是确认：

- bot 能不能接手正文创建
- 返回里有没有稳定的 `doc_id` / `doc_url`

在这次实践里，答案是可以。

### 第二步：读取文档

```bash
lark-cli docs +fetch \
  --as bot \
  --doc <DOC_URL> \
  --format pretty
```

这一步不是多余的。

对 Agent 来说，写完再读一遍非常重要，因为它可以立刻暴露：

- 正文有没有真写进去
- 标题和正文有没有重复
- Markdown 转义有没有写坏

这次实践里就踩到了一个很典型的坑：

- 如果你在 shell 字符串里直接硬塞字面量 `\n`，飞书里可能真的会看到 `\n`

更稳妥的做法是：

- heredoc
- 文件读入
- 真换行，不赌 shell 转义

### 第三步：追加正文

```bash
lark-cli docs +update \
  --as bot \
  --doc <DOC_URL> \
  --mode append \
  --markdown "$UPDATE_MARKDOWN"
```

到这一步，Agent 已经可以做三件很实用的事：

- 创建计划文档
- 追加执行进度
- 产出最终摘要

也就是说，只靠 `docs +create / +fetch / +update`，其实就已经有一个很能打的文档自动化底座了。

### 第四步：加评论

真正让文档交互“活起来”的，不是正文，而是评论。

这里要明确一个概念：

- 正文编辑走 `docs`
- 评论相关走 `drive`

全文评论：

```bash
lark-cli drive +add-comment \
  --as bot \
  --doc <DOC_URL> \
  --full-comment \
  --content '[{"type":"text","text":"comment from lark-cli bot"}]'
```

局部评论：

```bash
lark-cli drive +add-comment \
  --as bot \
  --doc <DOC_URL> \
  --selection-with-ellipsis 'docs +search rejected bot identity' \
  --content '[{"type":"text","text":"local comment: user-only boundary"}]'
```

如果你的 Agent 最后需要“在文档上给建议”，这一步几乎是必测项。

### 第五步：回复评论

评论能写进去还不够，真实协作里通常还需要继续在评论线程下跟进。

```bash
lark-cli drive file.comment.replys create \
  --as bot \
  --params '{"file_token":"<DOC_ID>","comment_id":"<COMMENT_ID>","file_type":"docx"}' \
  --data '{"content":{"elements":[{"type":"text_run","text_run":{"text":"已收到，这条用于评论回复链路测试。"}}]}}'
```

这一步对于 Agent 的意义是：

- 它不只是“往正文里写字”
- 它还能进入 review 线程继续交互

这会让很多“Agent 辅助审阅”的场景一下子变得顺手。

### 第六步：给人权限

如果文档只是 bot 能看，那这条链还是没闭环。

更实用的 quickstart 方式是把权限拆成两层：

- 负责人：`full_access`
- 协作群：`view`

给用户可管理权限：

```bash
lark-cli drive permission.members create \
  --as bot \
  --params '{"token":"<DOC_ID>","type":"docx","need_notification":true}' \
  --data '{"member_id":"<OPEN_ID>","member_type":"openid","perm":"full_access","type":"user"}'
```

给群聊基础可读权限：

```bash
lark-cli drive permission.members create \
  --as bot \
  --params '{"token":"<DOC_ID>","type":"docx","need_notification":false}' \
  --data '{"member_id":"<OPENCHAT_ID>","member_type":"openchat","perm":"view","type":"chat"}'
```

这比一上来研究复杂权限矩阵更适合 Agent 开发初期。

### 第七步：把链接发出去

文档能力真正“如虎添翼”的最后一步，不是继续编辑，而是送达。

这一步恰好可以用 ChatTool 留下来的最短消息链：

```bash
chattool lark send <OPENCHAT_ID> "<DOC_URL>" -t chat_id
```

或者如果已经配置了默认群聊：

```bash
chattool lark send -t chat_id "<DOC_URL>"
```

这说明 `chattool lark send` 虽然功能极简，但依然很值：

- 文档建好后把链接发给人
- 权限配好后把链接发到群里
- 做联调时快速验证默认用户 / 默认群聊

---

## 这条文档链路对 Agent 开发意味着什么

如果从 Agent 交互角度看，这条实践最有价值的不是“我会了几个命令”，而是它把飞书交互拆成了很清楚的几个阶段：

### 1. 内容阶段

用 `docs` 负责：

- 创建
- 读取
- 更新

### 2. 讨论阶段

用 `drive` 负责：

- 评论
- 回复

### 3. 权限阶段

还是用 `drive` 负责：

- 给具体人更高权限
- 给群更宽范围的可读权限

### 4. 送达阶段

用 `chattool lark send` 负责：

- 把文档链接发出去

这种分层非常适合 Agent，因为每一层都很容易单独测试、单独回滚、单独做权限收敛。

---

## 再补两个非常实用的边界提醒

### 1. 搜索更像 user 路线

如果只是“我已经有文档 URL 了”，bot 流程已经很好用。  
但如果问题变成“帮我找那篇文档”，就要尽早接受一件事：

- `docs +search` 更像 user 身份能力

所以工作流设计上最好一开始就拆成：

- known doc -> bot
- discovery -> user

### 2. `/wiki/...` 链接要先解析

如果用户给你的不是 `/docx/...`，而是 `/wiki/...`，不要直接把 token 当文档 token 用。

先走：

```bash
lark-cli wiki spaces get_node --params '{"token":"<WIKI_TOKEN>"}'
```

先拿到真实 `obj_type` 和 `obj_token`，再决定是继续走 `docs`、`base`，还是别的命令面。

这一步对于 Agent 很重要，因为真实用户往往更常贴知识库链接，而不是底层对象链接。

---

## 小结

如果只看“能不能做飞书交互”，当然可以直接自己包 SDK。  
但如果目标是**让 Agent 快速、稳定、可调试地接入飞书**，官方 SDK + 官方 CLI 这套组合会省很多事。

尤其是文档这条链路，它已经足够支撑一条非常实用的 Agent 工作流：

> **创建 -> 读取 -> 更新 -> 评论 -> 回复 -> 权限 -> 送达**

对 Agent 开发来说，这种感觉确实有点像“如虎添翼”：

- 正文有落点
- review 有线程
- 权限有边界
- 结果能送达

先把这条线跑顺，再往上扩搜索、知识库列表、位置移动、多维表格，会稳很多。
