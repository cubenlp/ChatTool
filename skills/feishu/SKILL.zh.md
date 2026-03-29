---
name: feishu
description: Use for Feishu/Lark work in ChatTool. Default to official lark-cli, route document body edits to docs, comments and permissions to drive, wiki links to wiki, IM sending/reply/search to im, and keep chattool lark only for info/send/chat debug and delivery.
version: 1.0.0
---

# Feishu Skill

面向 ChatTool 仓库内的飞书工作，目标是让模型先快速理解边界，再选对命令。

英文版见：`skills/feishu/SKILL.md`

## 何时使用

当任务涉及以下任一内容时使用本 skill：

- Feishu / Lark CLI
- 飞书消息发送、reply、chat_id / open_id 判断
- 飞书文档创建、读取、更新、评论、授权
- wiki 链接解析
- `chattool lark` 与 `lark-cli` 的边界判断
- `chattool setup lark-cli` 配置迁移

## 先记住边界

- 默认入口是官方 `lark-cli`
- `chattool lark` 只保留最短调试链路：`info` / `send` / `chat`
- 不要再把 ChatTool 当成“大而全飞书 CLI”

仓库内高价值参考：

- `docs/blog/agent-cli/lark-cli-guide.md`
- `docs/blog/agent-cli/feishu-cli-doc-practice.md`
- `docs/blog/lark-message-session-debug.md`
- `docs/tools/lark/index.md`
- `lark-cli/`

## 默认工作流

1. 先判断这是配置问题、消息问题、文档问题，还是 wiki/权限问题
2. 默认先看 `lark-cli` 路线，不先扩 `chattool lark`
3. 有副作用的命令先加 `--dry-run`
4. 需要 user 身份时，再走 `lark-cli auth login`

配置与认证起点：

```bash
chattool setup lark-cli
lark-cli auth status
lark-cli auth login --recommend
```

## 命令分流

### 1. 最短调试与送达

只在这几种场景用 `chattool lark`：

- 快速验证 bot 凭证：`chattool lark info`
- 发送一条最简单文本消息：`chattool lark send`
- 在本地终端调 prompt / session：`chattool lark chat`

不要再把文档、评论、权限、搜索、reply 主流程放回 `chattool lark`。

### 2. 消息与会话

优先用 `lark-cli im`：

- 发送消息：`lark-cli im +messages-send`
- 回复消息：`lark-cli im +messages-reply`
- 查群或找 `chat_id`：`lark-cli im +chat-search`
- 查看某会话消息：`lark-cli im +chat-messages-list`
- 查 thread：`lark-cli im +threads-messages-list`

关键概念：

- `message_id`: 一条消息，reply 依赖它
- `chat_id`: 一个会话/群聊，发消息常用它
- `open_id`: 用户对象，发私聊可直接用
- `receive_id_type`: 决定当前是在给谁发

经验规则：

- 新发消息：优先想清楚 `chat_id` 还是 `open_id`
- reply：看 `message_id`，不是 `chat_id`
- 调试最短送达：可以先用 `chattool lark send`
- 需要更完整的返回字段时，优先用 `lark-cli im +messages-send`

### 3. 文档正文

正文编辑走 `docs`：

- `lark-cli docs +create`
- `lark-cli docs +fetch`
- `lark-cli docs +update`

### 4. 评论与权限

评论、回复评论、授权走 `drive`：

- `lark-cli drive +add-comment`
- `lark-cli drive file.comment.replys create`
- `lark-cli drive file.comments list`
- `lark-cli drive file.comments patch`
- `lark-cli drive permission.members create`

### 5. Wiki 链接

wiki URL / token 先解析，不要直接当 doc token：

- `lark-cli wiki spaces get_node`

## 当前可直接采用的默认认识

这些结论和当前仓库文档是一致的，可先当默认假设：

- 文档正文链路通常先试 bot：`docs +create / +fetch / +update`
- 评论与基础授权通常也先试 bot：`drive +add-comment` / `file.comment.replys create` / `permission.members create`
- 搜索、发现、浏览类动作更可能需要 user 身份
- shell 里不要用字面量 `\n` 硬拼 Markdown；优先用真实换行或 heredoc
- 评论创建后立即 list，可能需要短暂重试

## 决策规则

1. 配置迁移或安装：先 `chattool setup lark-cli`
2. 发最短文本消息：可用 `chattool lark send`
3. 需要 reply、搜索、message/chat/thread 定位：转 `lark-cli im`
4. 需要文档正文：转 `lark-cli docs`
5. 需要评论、权限、评论回复：转 `lark-cli drive`
6. 需要 wiki 解析：转 `lark-cli wiki`

## 对模型最重要的约束

- 先选对命令面，再写命令
- 不要重复设计一套平行 Feishu CLI
- 不确定参数结构时，先看 `--help` 或 `schema`
- 优先给出最小可执行路径，不要先展开大而全说明
