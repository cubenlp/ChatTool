# 飞书 CLI 使用教程

`chattool lark` 现在只保留一个极小的遗留命令面：

- `chattool lark info`
- `chattool lark send`
- `chattool lark chat`

设计原则很简单：

- ChatTool 只保留“最短调试链路”
- 真正的飞书 / Lark 自动化默认直接使用官方 `lark-cli`

## 为什么只保留这三个

- `info`
  - 用当前 ChatTool Feishu 配置做最快的凭证验活
- `send`
  - 保留一条最短的文本消息发送路径，方便临时调试
- `chat`
  - 在本地终端里复用 ChatTool 的会话能力调提示词

像文档、上传、reply、listen、scopes、calendar、task、bitable、im、troubleshoot 这些能力，都不再由 `chattool lark` 维护。

## 前置准备

先准备 ChatTool 的 Feishu 配置：

```bash
chatenv init -t feishu
```

或手工设置：

```bash
export FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
export FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

如果你希望 `send` 可以省略接收者，再配置：

```bash
chatenv set FEISHU_DEFAULT_RECEIVER_ID=f25gc16d
chatenv set FEISHU_DEFAULT_CHAT_ID=oc_xxxxx
```

## `-e/--env`

三个保留命令都支持 `-e/--env`：

```bash
chattool lark info -e ~/.config/chattool/envs/Feishu/.env
chattool lark info -e work
```

支持：

- `.env` 文件路径
- `Feishu` 类型下已保存的 profile 名称

优先级：

1. 命令参数
2. `-e/--env`
3. 当前进程环境变量
4. `envs/Feishu/.env`
5. 默认值

## 最小用法

### 验证凭证

```bash
chattool lark info
chattool lark info -e work
```

### 发送文本消息

```bash
chattool lark send "你好"
chattool lark send f25gc16d "你好"
chattool lark send oc_xxxxx "群通知" -t chat_id
chattool lark send -t chat_id "群通知"
```

如果配置了 `FEISHU_DEFAULT_RECEIVER_ID`，单参数形式会被视为消息文本，自动发给默认用户。

如果配置了 `FEISHU_DEFAULT_CHAT_ID`，则可以直接：

```bash
chattool lark send -t chat_id "群通知"
```

这时 CLI 会自动把消息发给默认群聊。

### 本地调试 AI 对话

```bash
chattool lark chat
chattool lark chat --system "你是一名飞书助手"
chattool lark chat --max-history 5
chattool lark chat --user debug_user
```

内置命令：

- `/clear`
- `/quit`

## 其余能力的默认路线

推荐直接执行：

```bash
chattool setup lark-cli
lark-cli auth login --recommend
```

进一步阅读：

- `docs/blog/agent-cli/lark-cli-guide.md`
- `docs/blog/agent-cli/feishu-cli-doc-practice.md`
- `docs/env/lark-cli.md`
- `skills/feishu/SKILL.md`
