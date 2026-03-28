# Lark CLI 实战：真正把飞书文档创建、读取、更新、评论跑一遍

这一篇不再按“读完 README 后复述功能表”的方式写，而是直接讲一条更有实践意义的路线：

> **先把 `lark-cli` 装好，再用真实命令把飞书文档的创建、读取、更新、评论跑通，并明确哪些能力必须走 user 身份。**

本文基于 **2026-03-29** 在 ChatTool 工作区里的真实操作整理，重点不是列举命令，而是回答几个更实际的问题：

- 先装好以后，文档能力到底怎么串起来用？
- 没有 user login 时，bot 身份能做到哪一步？
- 哪些命令看起来都叫“docs”，实际上权限边界完全不同？
- 在 shell 里直接拼 Markdown，有哪些很容易踩坑的地方？

---

## 先把工具装好

如果你已经在用 ChatTool，最直接的方式不是手工抄配置，而是直接：

```bash
chattool setup lark-cli
```

这条命令现在会做几件事：

1. 检查 `Node.js >= 20` 和 `npm`
2. 检查本机是否已经装过 `lark-cli`
3. 如果已经装过，先打印当前版本；默认跳过重复下载
4. 复用 ChatTool 当前生效的 Feishu 配置写入 `lark-cli`

这一点对日常开发很重要，因为你往往不是第一次装，而是反复调试：

- 已安装时先看版本
- 只有你明确确认，才去重新 `npm install -g`
- 否则直接跳过下载，继续做配置或后续调试

默认配置位置：

```text
~/.lark-cli/config.json
```

如果你是从 ChatTool 复用配置，来源默认是：

```text
~/.config/chattool/envs/Feishu/.env
```

或者你通过：

```bash
chattool env cat -t Feishu
```

看到的当前生效 Feishu 配置。

---

## 先分清 bot 和 user

很多人第一次用 `lark-cli` 时，最容易混淆的一点是：

> **“已经配置了 app_id / app_secret” 不等于 “已经有 user 身份”。**

我在本地跑完配置后，先看状态：

```bash
lark-cli auth status
```

返回的是：

```json
{
  "identity": "bot",
  "note": "No user logged in. Only bot (tenant) identity is available for API calls."
}
```

这意味着当前状态是：

- app 已配置
- bot 身份可用
- 但还没有 user login

这件事非常关键，因为后面飞书文档相关命令，**有些 bot 能做，有些只能 user 做**。

---

## 一条真正能跑通的文档链路

下面这组命令，是我在当前环境里真实跑过的。

目标很简单：

1. 创建文档
2. 读回内容
3. 追加更新
4. 添加全文评论
5. 添加局部高亮评论
6. 解决 / 恢复评论
7. 添加基础协作者权限
8. 读取评论

---

## 第一步：用 bot 创建文档

先说结论：

> **`docs +create` 可以直接用 bot 身份。**

实际命令：

```bash
lark-cli docs +create \
  --as bot \
  --title "ChatTool Lark CLI Practice 20260329-031654" \
  --markdown "# ChatTool Lark CLI Practice\n\n- created by lark-cli bot\n- branch: rex/feishu-doc"
```

这次真实返回成功：

```json
{
  "ok": true,
  "identity": "bot",
  "data": {
    "doc_id": "My7IdiXGbotSsSxYPAEcvYLnnWg",
    "doc_url": "https://www.feishu.cn/docx/My7IdiXGbotSsSxYPAEcvYLnnWg",
    "message": "文档创建成功"
  }
}
```

这说明至少在“创建一份新文档”这个动作上，bot 身份是够用的。

---

## 第二步：把文档读回来

创建成功后，立刻可以读：

```bash
lark-cli docs +fetch \
  --as bot \
  --doc https://www.feishu.cn/docx/My7IdiXGbotSsSxYPAEcvYLnnWg \
  --format pretty
```

这一步也真实成功了。

不过这里马上踩到一个非常典型的 shell 坑：

```text
# ChatTool Lark CLI Practice\n\n- created by lark-cli bot\n- branch: rex/feishu-doc
```

也就是说，我最开始在命令行里直接传的 `\n`，最终被当成了字面文本，而不是换行。

### 这说明什么

如果你直接在 shell 里把 Markdown 塞进一个参数字符串，**很容易把 `\n` 当普通字符传进去**。

更稳妥的写法是先用 heredoc 组装内容：

```bash
MARKDOWN=$(cat <<'EOF'
# ChatTool Lark CLI Practice

- created by lark-cli bot
- branch: rex/feishu-doc
EOF
)

lark-cli docs +create \
  --as bot \
  --title "ChatTool Lark CLI Practice" \
  --markdown "$MARKDOWN"
```

这比在一行 shell 命令里硬塞转义字符可靠得多。

---

## 第三步：追加更新文档

接下来我继续用 bot 身份追加内容：

```bash
lark-cli docs +update \
  --as bot \
  --doc https://www.feishu.cn/docx/My7IdiXGbotSsSxYPAEcvYLnnWg \
  --mode append \
  --markdown "
## Update Round 1

- appended by lark-cli
- operation: docs +update --mode append"
```

返回成功：

```json
{
  "ok": true,
  "identity": "bot",
  "data": {
    "message": "文档更新成功（append模式）",
    "mode": "append",
    "success": true
  }
}
```

这说明在当前环境下，下面这条 bot 路径是可行的：

```text
docs +create -> docs +fetch -> docs +update
```

如果你的目标是：

- 让 agent 自动写计划
- 自动把执行进度追加到文档
- 自动产出结果摘要

那么这条 bot 路径已经足够有用了。

---

## 第四步：给文档加全文评论

飞书文档工作流里，评论非常关键，因为这直接关系到 review。

这里要注意：

- 文档内容编辑走 `docs`
- 文档评论走 `drive`

实际命令：

```bash
lark-cli drive +add-comment \
  --as bot \
  --doc https://www.feishu.cn/docx/My7IdiXGbotSsSxYPAEcvYLnnWg \
  --full-comment \
  --content '[{"type":"text","text":"comment from lark-cli bot"}]'
```

真实返回：

```json
{
  "ok": true,
  "identity": "bot",
  "data": {
    "comment_id": "7622387805116697557",
    "comment_mode": "full",
    "file_type": "docx"
  }
}
```

这一点很重要，因为它说明：

> **bot 不只是能改正文，也能直接往 docx 上写评论。**

---

## 第五步：给一段正文加局部高亮评论

如果你只是做 quickstart，全文评论还不够，因为真实 review 更常见的是“圈住一段话再评论”。

这一步我直接对文档中的一句正文做局部评论：

```bash
lark-cli drive +add-comment \
  --as bot \
  --doc https://www.feishu.cn/docx/My7IdiXGbotSsSxYPAEcvYLnnWg \
  --selection-with-ellipsis 'docs +search rejected bot identity' \
  --content '[{"type":"text","text":"local comment: user-only boundary"}]'
```

CLI 会先自动定位正文块：

```text
Locate-doc matched 1 block(s); using match #1
Creating local comment in My7I...nnWg
```

这条链路真实跑通后，评论列表里可以看到：

- `is_whole = false`
- `quote = "docs +search rejected bot identity and is user-only"`

这比全文评论更接近“给文档做 review”时的实际体验。

---

## 第六步：解决评论，再恢复评论

评论不只是“写进去”，还要能进入已解决状态。

我先把全文评论标记为已解决：

```bash
lark-cli drive file.comments patch \
  --as bot \
  --params '{"file_token":"My7IdiXGbotSsSxYPAEcvYLnnWg","comment_id":"7622387805116697557","file_type":"docx"}' \
  --data '{"is_solved":true}'
```

返回成功后，再列评论能看到：

- `is_solved = true`
- `solver_user_id` 已出现

随后我又把它恢复回来：

```bash
lark-cli drive file.comments patch \
  --as bot \
  --params '{"file_token":"My7IdiXGbotSsSxYPAEcvYLnnWg","comment_id":"7622387805116697557","file_type":"docx"}' \
  --data '{"is_solved":false}'
```

所以 quickstart 至少可以确认：

- 评论创建可用
- 评论 solve 可用
- 评论 restore 可用

---

## 第七步：给文档加基础协作者权限

权限这块如果做全，会很复杂；但 quickstart 至少可以先验证两种最基础的场景：

- 给一个用户加只读权限
- 给一个群聊加只读权限

我直接给默认飞书用户加了 `view` 权限：

```bash
lark-cli drive permission.members create \
  --as bot \
  --params '{"token":"My7IdiXGbotSsSxYPAEcvYLnnWg","type":"docx","need_notification":false}' \
  --data '{"member_id":"9dd3d3ea","member_type":"userid","perm":"view","type":"user"}'
```

真实返回里能看到：

- `member_id = 9dd3d3ea`
- `perm = view`
- `perm_type = container`

群聊权限也可以用同一条 API，只是把 `member_type` / `type` 切到群聊：

```bash
lark-cli drive permission.members create \
  --as bot \
  --params '{"token":"My7IdiXGbotSsSxYPAEcvYLnnWg","type":"docx","need_notification":false}' \
  --data '{"member_id":"<OPENCHAT_ID>","member_type":"openchat","perm":"view","type":"chat"}'
```

也就是说，quickstart 里“权限基础的”这一步，最合适的就是：

- 给一个用户加 `view`
- 给一个群聊加 `view`
- 先不碰 owner transfer
- 先不碰更复杂的 department / wiki 权限

---

## 第八步：读取评论时，不要假设“刚写完就立刻能列出来”

紧接着我马上执行：

```bash
lark-cli drive file.comments list \
  --as bot \
  --params '{"file_token":"My7IdiXGbotSsSxYPAEcvYLnnWg","file_type":"docx"}'
```

第一次返回的是空列表。

两秒后再读一次，才拿到了评论：

```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "comment_id": "7622387805116697557",
        "is_whole": true,
        "reply_list": {
          "replies": [
            {
              "content": {
                "elements": [
                  {
                    "text_run": {
                      "text": "comment from lark-cli bot"
                    }
                  }
                ]
              }
            }
          ]
        }
      }
    ]
  }
}
```

这件事的实践意义很强：

- **评论写入成功**
- **列表接口未必立刻可见**
- 如果你要把“写评论 -> 读评论 -> 汇总评论”串成自动流程，最好带一个短重试

也就是说，不要把第一次空列表立刻判成失败。

---

## 一个真实踩出来的身份边界

前面几步基本都能用 bot 跑通，但到了搜索这里，情况就不一样了。

我真实执行了：

```bash
lark-cli docs +search --as bot --query ChatTool --page-size 5
```

CLI 直接报错：

```text
Error: --as bot is not supported, this command only supports: user
```

这说明：

> **`docs +search` 是 user-only，不要指望 bot 帮你做文档搜索。**

这个边界非常适合写进工作流设计：

- bot 适合“已知 doc_id / doc_url 后的自动执行”
- user 更适合“搜索、发现、浏览、授权范围内查找”

如果你后面要做飞书任务编排，这会直接影响入口设计：

- 已有项目主文档时，bot 可以稳定接手
- 如果用户只说“找一下那篇文档”，往往还是得走 user 身份

---

## 所以，飞书文档能力到底怎么拆最实用

如果只从“实战价值”出发，我现在更推荐这样理解 `lark-cli` 的文档面：

### 1. `docs`

负责正文内容工作流：

- `docs +create`
- `docs +fetch`
- `docs +update`

这条线非常适合：

- 计划文档
- 阶段进展记录
- 结果摘要
- 验收说明

### 2. `drive`

负责评论和文件侧动作：

- `drive +add-comment`
- `drive file.comments list`

这条线更适合：

- review
- 留批注
- 读取评论线程

### 3. `wiki`

负责从知识库节点解析真实对象类型和 token。

如果你拿到的是 `/wiki/...` 链接，不要直接猜它是不是 docx，要先解到真实对象。

### 4. `base`

负责多维表格，不属于本文重点，但如果你后面要做任务面板、状态板、任务总览，最终会落到这条线上。

---

## 如果你要做“飞书文档工作流”，先记住这几个经验

### 经验 1：先拿稳定文档 ID，再谈自动化

只要你已经有了 `doc_url` 或 `doc_id`，bot 路线就很顺：

- 创建
- 读取
- 追加
- 评论

而“搜索文档”这一步更像 user 路线，不适合混在 bot 自动链路里硬做。

### 经验 2：正文和评论不是一套命令面

很多人会自然地以为“文档评论”也在 `docs` 下面，其实不是。

- 正文编辑：`docs`
- 评论：`drive`

这个边界要在设计里提前接受。

### 经验 3：不要在 shell 里硬写带 `\n` 的 Markdown

这是今天最容易踩的坑之一。

更稳妥的做法：

- heredoc
- 临时变量
- 或者先把内容生成到文件，再读进 shell 变量

### 经验 4：局部评论是 quickstart 里最值得保留的一步

如果你只做全文评论，很难看出这条链路到底能不能支撑真正的 review。

局部评论更有价值，因为它同时验证了：

- 正文定位
- block 定位链路
- quote 回显
- 评论列表返回结构

### 经验 5：写完评论后，读取时给一点延迟

如果你要把这套东西做成 agent 流程，建议把评论列表读取做成：

1. 立即读一次
2. 若为空，短暂等待
3. 再读一次

否则很容易把“延迟可见”误判成“写入失败”。

---

## 对 ChatTool 的现实意义

站在 ChatTool 当前这条路线看，`lark-cli` 最值得用的不是“覆盖面大”这件事本身，而是：

> **它已经足够把飞书文档工作流拆成一条可执行的链。**

至少对于文档这块，已经可以很明确地分成两类：

- ChatTool 负责：
  - `chattool setup lark-cli`
  - 配置复用
  - 最短调试链路
- 官方 `lark-cli` 负责：
  - 文档创建
  - 文档读取
  - 文档更新
  - 文档评论
  - 后续 wiki / base / drive 扩展

这比在 ChatTool 里继续维护一整套平行的飞书文档 CLI，更有现实意义。

---

## 最后给一条最实用的起步路线

如果你现在就想把飞书文档能力真正用起来，建议按这个 quickstart 顺序：

```bash
chattool setup lark-cli
lark-cli auth status
```

先确认当前是 bot-only 还是已经 user login。

然后直接从这条链开始：

```bash
lark-cli docs +create --as bot ...
lark-cli docs +fetch --as bot --doc <DOC_URL>
lark-cli docs +update --as bot --doc <DOC_URL> --mode append ...
lark-cli drive +add-comment --as bot --doc <DOC_URL> --full-comment ...
lark-cli drive +add-comment --as bot --doc <DOC_URL> --selection-with-ellipsis "..." ...
lark-cli drive file.comments patch --as bot ...
lark-cli drive permission.members create --as bot ...
lark-cli drive permission.members create --as bot --data '{"member_type":"openchat","type":"chat",...}'
lark-cli drive file.comments list --as bot --params '{"file_token":"<DOC_ID>","file_type":"docx"}'
```

如果你后面需要“搜索文档”，再补：

```bash
lark-cli auth login --recommend
lark-cli docs +search --as user --query "<KEYWORD>"
```

一句话总结：

> **飞书文档 quickstart 最实用的切法，不是先学完整命令树，而是先把 bot 可跑通的“创建 -> 读取 -> 更新 -> 全文评论 -> 局部评论 -> solve/restore -> 基础权限”打通，再把 search 这类 user-only 能力单独补上。**
