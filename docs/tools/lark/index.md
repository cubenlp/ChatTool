# 飞书 CLI 使用教程

这页只讲一件事：如何直接用 `chattool lark` 把飞书机器人跑起来、验证通、发出消息，并排查权限或监听问题。

如果你的目标是“先用起来”，优先走 CLI，不要先写 Python 脚本。

## CLI 能力范围

当前推荐的飞书入口是 `chattool lark`，已覆盖这些日常动作：

- 验证机器人凭证与激活状态：`info`
- 查看应用权限：`scopes`
- 发送文本、图片、文件、卡片、富文本：`send`
- 单独上传图片或文件：`upload`
- 引用回复已有消息：`reply`
- 监听长连接事件做调试：`listen`
- 在本地终端调试 AI 会话：`chat`
- 创建云文档并通知目标用户：`notify-doc`
- 读取和修改云文档分享权限：`doc perm-public-get/set`、`doc perm-member-list/add`
- 多维表格基础操作：`bitable app/table/field/record ...`
- 日历基础操作：`calendar primary/event/freebusy ...`
- 任务基础操作：`task ...`、`task tasklist ...`
- 消息读取与资源下载：`im list`、`im download`
- 常见排障入口：`troubleshoot doctor/check-scopes/check-events/check-card-action`

如果你的目标是继续扩展 Feishu 能力，而不是只执行现有命令，请先阅读：

- `skills/feishu/SKILL.md`
- `docs/blog/agent-cli/lark-cli-guide.md`
- `docs/design/feishu-cli.md`

## 前置准备

先安装工具依赖：

```bash
pip install "chattool[tools]"
```

然后初始化飞书凭证：

```bash
chattool env init -t feishu
```

如果你不想走交互式，也可以直接设置环境变量：

```bash
export FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
export FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

!!! warning "输入边界要清晰"
    `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET` 只用于放飞书凭证。  
    如果当前运行环境同时被 OpenClaw、消息网关或其他入口复用，不要再用新的环境变量传接收者、消息内容、文件路径这类业务参数。  
    这些输入应直接放在 CLI 参数里，避免变量冲突和语义歧义。

如果你经常发消息给同一个默认接收者，可以直接配置：

```bash
chattool env set FEISHU_DEFAULT_RECEIVER_ID=f25gc16d
```

配置后，`chattool lark send` 可以省略接收者参数。

如果你要跑 CLI 真实测试，且需要和默认接收者分开，才额外配置：

```bash
chattool env set FEISHU_TEST_USER_ID=f25gc16d
chattool env set FEISHU_TEST_USER_ID_TYPE=user_id
```

## `-e/--env`

如果你不想依赖当前 shell 里的环境变量，可以给子命令显式传一个配置来源：

```bash
chattool lark info -e ~/.config/chattool/envs/Feishu/.env
chattool lark info -e work
```

`-e/--env` 支持两种形式：

- `.env` 文件路径
- `Feishu` 类型下通过 `chatenv save -t feishu` 保存过的 profile 名称，例如 `work`

这适合多套飞书应用来回切换，或者在当前 shell 环境比较脏的时候，明确指定一份配置来执行。

`chattool lark` 的运行时优先级固定为：

1. 命令参数本身
2. `-e/--env` 显式指定的 `.env` 文件或 `Feishu` profile
3. 当前进程环境变量
4. `envs/Feishu/.env`
5. 代码默认值

## 最短工作流

### 1. 验证凭证

```bash
chattool lark info
chattool lark info -e work
```

这一步用于确认：

- `FEISHU_APP_ID` / `FEISHU_APP_SECRET` 是否正确
- 机器人是否已激活
- 当前凭证是否能成功访问飞书 OpenAPI

### 2. 检查权限

```bash
chattool lark scopes
chattool lark scopes -f im
chattool lark scopes -g
chattool lark scopes -a -g
```

建议至少先检查消息相关权限是否已授权，再发消息。

如果你只是排查发消息失败，先跑这一条通常最快：

```bash
chattool lark scopes -f im
```

如果 `troubleshoot check-scopes` 或 `doctor` 把某个分类标成 `missing`，应优先把它视为权限问题，而不是直接怀疑 CLI 参数或业务逻辑。

### 3. 发一条文本消息

```bash
chattool lark send "你好，世界"
chattool lark send rexwzh "你好，世界"
chattool lark send rexwzh "你好，世界" -e work
```

默认接收者类型是 `user_id`。如果你要给群发消息，需要显式指定 `chat_id`：

```bash
chattool lark send oc_xxxxx "群通知" -t chat_id
```

如果你拿到的是 `open_id`、`email` 或 `union_id`，也可以直接切换：

```bash
chattool lark send ou_xxxxx "你好" -t open_id
chattool lark send someone@example.com "你好" -t email
```

如果 `send` 返回权限错误码，CLI 会继续做两件事：

- 自动复用 scopes 诊断逻辑，判断是否真的是权限缺失
- 若已配置 `FEISHU_DEFAULT_RECEIVER_ID`，尽量自动发送权限引导卡
- 若 CLI 真实测试显式配置了 `FEISHU_TEST_USER_ID`，也可用它做隔离排障

如果连自动发卡也失败，CLI 仍会把权限引导卡 JSON 导出到 `/tmp/chattool-lark-permission-card.json`，方便继续排障。

## 发送不同类型的消息

### 文本

```bash
chattool lark send "测试消息"
chattool lark send <receiver> "测试消息"
```

### 图片

```bash
chattool lark send <receiver> --image ./photo.jpg
```

### 文件

```bash
chattool lark send <receiver> --file ./report.pdf
```

### 卡片消息

```bash
chattool lark send <receiver> --card ./card.json
```

### 富文本消息

```bash
chattool lark send <receiver> --post ./post.json
```

`send` 会自动根据参数决定发送哪种消息。文本和文件类输入不要混在环境变量里，直接通过命令行参数传入。

如果已配置 `FEISHU_DEFAULT_RECEIVER_ID`，单参数形式会被视为消息文本，自动发给默认用户。

## 只上传资源，不立刻发消息

如果你只想先拿到 `image_key` 或 `file_key`，用 `upload`：

```bash
chattool lark upload ./photo.jpg
chattool lark upload ./report.pdf
chattool lark upload ./data.bin -t file
```

这通常用于两类场景：

- 先上传资源，再拼卡片 JSON
- 先拿 key，再嵌入富文本结构

## 引用回复已有消息

```bash
chattool lark reply om_xxxxxx "收到，已处理"
```

这里的 `message_id` 来自你已经收到或查询到的那条飞书消息。

## 调试消息接收链路

如果你怀疑“机器人能发不能收”，直接开监听：

```bash
chattool lark listen
chattool lark listen -v
chattool lark listen -l DEBUG
```

使用 `listen` 之前，需要先在飞书后台确认：

- 已开启长连接模式
- 已订阅 `im.message.receive_v1`
- 已开通对应事件权限
- 新权限或事件配置已经发布生效

## 本地调试 AI 对话

`chattool lark chat` 不经过飞书发消息，只是在终端里复用会话能力，适合先调提示词和上下文。

```bash
chattool lark chat
chattool lark chat --system "你是一名飞书助手"
chattool lark chat --max-history 5
chattool lark chat --user debug_user
```

内置命令：

- `/clear`：清空当前用户的历史对话
- `/quit`：退出终端会话

## 云文档

除了消息收发，`chattool lark` 现在也支持一组云文档命令，基于飞书开放平台的 `docx` 服务端接口。

这组能力建议按双轨理解：

- 稳定正文轨：`notify-doc`、`doc append-text`、`doc append-file`
- 结构化 docx 轨：`doc parse-md`、`doc append-json`
- 协作权限轨：`doc perm-public-get/set`、`doc perm-member-list/add`

前者优先保证写入成功率，后者面向标题、列表、代码块、引用块等结构化能力。

当前 `parse-md -> append-json` 主线会保留代码块本身，但若 fenced code language 还不是 Feishu docx 可直接消费的数值枚举，写入前会先做安全归一化，避免因为语言字段不合法导致整批 block 写入失败。

## 专题 CLI

当前这些 topic 分组已经收口到 `chattool lark` 下：

- `chattool lark bitable ...`
  - 当前已支持 `app create`、`table list/create`、`field list/create`、`record list/create/batch-create`
- `chattool lark calendar ...`
  - 当前已支持 `primary`、`event create/list/get/patch/reply`、`freebusy list`
- `chattool lark im ...`
  - 当前已支持 `list --chat-id` 与 `download`
- `chattool lark task ...`
  - 当前稳定支持 `create/get/patch`、`tasklist create/list/get/tasks/add-members`
  - `task list` 受当前飞书凭证模式影响，若失败应优先判断为 token / scope 问题
- `chattool lark troubleshoot ...`
  - 当前已支持 `doctor`、`check-scopes`、`check-events`、`check-card-action`
  - `check-scopes` 可额外导出诊断卡片 JSON，或直接发送权限排障卡片
  - 当前权限诊断卡片是“跳转按钮卡片”；若要验证 `card.action.trigger` 这类回调交互，还需要单独检查卡片回传链路

后续扩展继续收敛在 `src/chattool/tools/lark/`，而不是重新拆成新的独立 skill 入口。

如果你想“一步创建文档并通知到人”，可以直接用：

```bash
chattool lark notify-doc "周报草稿" "今天完成了接口整理"
```

这条命令会：

- 创建一篇新文档
- 把正文追加进去
- 取回文档链接
- 把链接发给 `FEISHU_DEFAULT_RECEIVER_ID` 或 `--receiver` 指定的目标

### 创建文档

```bash
chattool lark doc create "周报草稿"
chattool lark doc create "会议纪要" --folder-token fldcnxxxxxxxx
```

### 查看文档信息

```bash
chattool lark doc get doccnxxxxxxxxxxxx
```

### 获取纯文本内容

```bash
chattool lark doc raw doccnxxxxxxxxxxxx
```

### 查看块结构

```bash
chattool lark doc blocks doccnxxxxxxxxxxxx
chattool lark doc blocks doccnxxxxxxxxxxxx --descendants
```

### 追加一段文本

```bash
chattool lark doc append-text doccnxxxxxxxxxxxx "今天完成了接口整理"
```

### 从本地文件追加正文

```bash
chattool lark doc parse-md ./daily.md
chattool lark doc parse-md ./daily.md -o ./daily.blocks.json
chattool lark doc append-json doccnxxxxxxxxxxxx ./daily.blocks.json
chattool lark doc append-file doccnxxxxxxxxxxxx ./daily.txt
chattool lark doc append-file doccnxxxxxxxxxxxx ./daily.md
chattool lark doc append-file doccnxxxxxxxxxxxx ./daily.md --batch-size 10
```

### 读取和设置文档权限

```bash
chattool lark doc perm-public-get doccnxxxxxxxxxxxx
chattool lark doc perm-public-set doccnxxxxxxxxxxxx \
  --share-entity same_tenant \
  --link-share-entity tenant_editable
chattool lark doc perm-member-add doccnxxxxxxxxxxxx f25gc16d --member-type userid --perm edit
chattool lark doc perm-member-list doccnxxxxxxxxxxxx
```

这组命令适合补齐这条最小工作流：

- 创建文档
- 追加正文
- 设置“企业内可编辑”或“指定成员可编辑”
- 再把文档链接发出去

常用枚举：

- `--link-share-entity`: `tenant_readable`、`tenant_editable`、`anyone_readable`、`anyone_editable`、`closed`
- `--share-entity`: `anyone`、`same_tenant`、`only_full_access`
- `--member-type`: `userid`、`openid`、`unionid`、`email` 等
- `--perm`: `view`、`edit`、`full_access`

### 创建后直接通知

```bash
chattool lark notify-doc "会议纪要" "这里是会议摘要"
chattool lark notify-doc "发布说明" "这里是更新内容" --receiver f25gc16d
chattool lark notify-doc "日报" --append-file ./daily.md
chattool lark notify-doc "日报" --append-file ./daily.md --open
chattool lark notify-doc "日报" --append-file ./daily.md --batch-size 10
```

说明：

- `chattool lark doc append-file` 适合往已有文档追加本地 `txt/md` 文件
- `chattool lark doc parse-md` 适合先检查 Markdown 将映射成哪些飞书 block
- `chattool lark doc append-json` 适合直接消费结构化 block JSON 写入文档
- `notify-doc --append-file` 适合创建文档、写入正文并把链接发给指定用户
- `.md` 文件在 `append-file` 这条命令里会先整理为飞书兼容的纯文本段落，再写入文档
- 批量写入失败时，CLI 会自动回退到单段写入，降低 `field validation failed` 这类错误的影响
- `--open` 会在发送成功后本地打开文档链接
- 若需要让接收方直接修改文档，先执行 `doc perm-public-set` 或 `doc perm-member-add`，再执行 `notify-doc` / `send`

如果你要把 scopes 缺失情况整理给应用维护者，可直接导出或发送诊断卡片：

```bash
chattool lark troubleshoot check-scopes --card-file ./scope-card.json
chattool lark troubleshoot check-scopes --send-card
chattool lark troubleshoot check-scopes --send-card --receiver <user_id>
```

这张卡片现在带有可点击按钮：

- `打开开放平台`：跳到飞书开放平台应用页，继续处理权限配置
- `查看权限文档`：打开官方权限文档，核对 scope 与能力映射

注意：卡片按钮只能把人带到授权/配置页面，不能在消息里直接为应用授予 scope。真正授权仍需在飞书开放平台完成。

!!! note "当前范围"
    这一版覆盖常用的文档基础能力、结构化追加和权限管理。  
    后续如果要继续扩，可以沿着 `chattool lark doc ...` 这条线补 `update`、`delete children`、`convert`、成员删除/更新，或继续往 drive/wiki 相关命令延伸。

## Command Reference

这部分只做命令索引，不展开教程，方便做编排或补能力时快速查可用 CLI。

### 基础与排障

- `chattool lark info`
- `chattool lark scopes`
- `chattool lark troubleshoot doctor|check-scopes|check-events|check-card-action`

### 消息

- `chattool lark send`
- `chattool lark reply`
- `chattool lark upload`
- `chattool lark listen`
- `chattool lark chat`

### 文档

- `chattool lark notify-doc`
- `chattool lark doc create|get|raw|blocks`
- `chattool lark doc append-text|append-file|parse-md|append-json`
- `chattool lark doc perm-public-get|perm-public-set`
- `chattool lark doc perm-member-list|perm-member-add`

### 其他专题

- `chattool lark bitable ...`
- `chattool lark calendar ...`
- `chattool lark im ...`
- `chattool lark task ...`

## API Reference

扩 CLI 时，优先查 Feishu 官方文档，而不是先写脚本试错：

- 发消息：`https://open.feishu.cn/document/server-docs/im-v1/message/create`
- 回复消息：`https://open.feishu.cn/document/server-docs/im-v1/message/reply`
- 上传图片：`https://open.feishu.cn/document/server-docs/im-v1/image/create`
- 上传文件：`https://open.feishu.cn/document/server-docs/im-v1/file/create`
- 创建文档：`https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/create`
- 创建 docx block：`https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block/create`
- 获取公开权限：`https://open.feishu.cn/document/server-docs/docs/drive-v1/permission-public/get`
- 更新公开权限：`https://open.feishu.cn/document/server-docs/docs/drive-v1/permission-public/patch`
- 列出协作者：`https://open.feishu.cn/document/server-docs/docs/drive-v1/permission-member/list`
- 添加协作者：`https://open.feishu.cn/document/server-docs/docs/drive-v1/permission-member/create`

如果当前能力缺口具有复用价值，优先判断是否应直接转向官方 `lark-cli`；只有确实属于 ChatTool 内部遗留实现维护时，才继续沉淀到 `src/chattool/tools/lark/`。

## 常见排查顺序

### 能否初始化

```bash
chattool lark info
```

如果这里就失败，优先检查凭证是否配置正确。

### 权限是否齐

```bash
chattool lark scopes -f im
```

如果发送失败或监听不到消息，先看消息相关权限和事件权限。

### 收发链路是否通

```bash
chattool lark send <receiver> "hello"
chattool lark listen -l DEBUG
```

先验证主动发送，再验证被动接收，排查效率最高。

## 一页速查

```bash
# 1. 配置凭证
chattool env init -t feishu

# 2. 验证机器人
chattool lark info
chattool lark info -e work

# 3. 查看消息相关权限
chattool lark scopes -f im

# 4. 发送文本
chattool lark send "你好"
chattool lark send rexwzh "你好"

# 5. 发送图片
chattool lark send rexwzh --image ./photo.jpg

# 6. 发送文件
chattool lark send rexwzh --file ./report.pdf

# 7. 引用回复
chattool lark reply om_xxxxxx "收到"

# 8. 调试监听
chattool lark listen -l DEBUG

# 9. 本地调提示词
chattool lark chat --system "你是一名飞书助手"
```
