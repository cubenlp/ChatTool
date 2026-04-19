---
name: feishu
description: "使用 lark-cli 和 chattool 与飞书/Lark 交互，处理消息发送、文档管理、wiki 解析和权限操作。用户提到发送飞书消息、回复线程、创建或编辑文档、解析 wiki 链接、调整权限或排查 bot 凭证时使用。"
version: 1.0.0
---

# Feishu Skill

通过 `lark-cli` 和 `chattool` 处理飞书/Lark 的消息、文档、wiki 与权限操作。默认以 `lark-cli` 为主，`chattool lark` 只用于最短调试与送达路径。

英文版见：`skills/feishu/SKILL.md`

## 命令分流

| 任务 | 命令 |
| :--- | :--- |
| 安装或迁移配置 | `chattool setup lark-cli` |
| 快速检查 bot 凭证 | `chattool lark info` |
| 发送一条简单文本 | `chattool lark send` |
| 本地 prompt / session 调试 | `chattool lark chat` |
| 发富文本、回复、搜索会话 | `lark-cli im` |
| 创建、读取、更新文档正文 | `lark-cli docs` |
| 评论与权限管理 | `lark-cli drive` |
| 解析 wiki 链接 | `lark-cli wiki spaces get_node` |

**不要**在 ChatTool 里再造一套完整的 Feishu CLI。`chattool lark` 只覆盖 `info`、`send`、`chat`。

## 工作流

1. 先判断任务属于配置、消息、文档、wiki 还是权限。
2. 默认从 `lark-cli` 开始。
3. 写操作优先加 `--dry-run`。
4. 只有 bot 身份不够时，才切到 user login。

### 认证初始化

```bash
chattool setup lark-cli
lark-cli auth status
lark-cli auth login --recommend
```

如果是 agent 协作登录，优先走非阻塞 device flow：

```bash
lark-cli auth login --recommend --no-wait
lark-cli auth login --device-code <DEVICE_CODE>
```

## 消息操作（`lark-cli im`）

```bash
lark-cli im +messages-send
lark-cli im +messages-reply
lark-cli im +chat-search
lark-cli im +chat-messages-list
lark-cli im +threads-messages-list
```

**ID 判断经验**：
- 新发消息：先分清是 `chat_id` 还是 `open_id`。
- 回复消息：围绕 `message_id`，不要只看 `chat_id`。
- 只做最短送达测试时：`chattool lark send` 足够。

## 文档正文（`lark-cli docs`）

```bash
lark-cli docs +create
lark-cli docs +fetch
lark-cli docs +update
```

## 评论与权限（`lark-cli drive`）

```bash
lark-cli drive +add-comment
lark-cli drive file.comment.replys create
lark-cli drive file.comments list
lark-cli drive file.comments patch
lark-cli drive permission.members create
```

## 关键参考

- `docs/blog/agent-cli/lark-cli-guide.md`
- `docs/blog/agent-cli/feishu-cli-doc-practice.md`
- `docs/blog/lark-message-session-debug.md`
- `docs/tools/lark/index.md`
- `lark-cli/`

## 当前默认认识

- 文档正文操作通常先试 bot：`docs +create / +fetch / +update`
- 基础评论与共享通常也先试 bot
- 搜索和发现类动作更可能需要 user 身份
- shell 里不要用字面量 `\n` 硬拼 Markdown，优先用真实换行或 heredoc
- 评论创建后马上查询，可能需要短暂重试
