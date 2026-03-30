---
name: feishu
description: Use for Feishu/Lark work in ChatTool. Default to official lark-cli, route document body edits to docs, comments and permissions to drive, wiki links to wiki, IM sending/reply/search to im, and keep chattool lark only for info/send/chat debug and delivery.
version: 1.0.0
---

# Feishu Skill

This is the fast mental model for Feishu/Lark work inside the ChatTool repo.

Chinese version: `skills/feishu/SKILL.zh.md`

## When To Use

Use this skill when the task involves any of these:

- Feishu / Lark CLI work
- sending messages, replying, or figuring out `chat_id` vs `open_id`
- creating, fetching, updating, commenting on, or sharing Feishu docs
- resolving wiki links
- deciding between `chattool lark` and `lark-cli`
- migrating Feishu config with `chattool setup lark-cli`

## Boundary First

- The default entrypoint is official `lark-cli`
- `chattool lark` is kept only for the shortest debug path: `info` / `send` / `chat`
- Do not rebuild a parallel “full Feishu CLI” inside ChatTool

High-value repo references:

- `docs/blog/agent-cli/lark-cli-guide.md`
- `docs/blog/agent-cli/feishu-cli-doc-practice.md`
- `docs/blog/lark-message-session-debug.md`
- `docs/tools/lark/index.md`
- `lark-cli/`

## Default Workflow

1. Classify the task: config, messaging, documents, wiki, or permissions
2. Start from `lark-cli` by default
3. Use `--dry-run` first for write operations
4. Only switch to user login when bot identity is not enough

Config and auth starting points:

```bash
chattool setup lark-cli
lark-cli auth status
lark-cli auth login --recommend
```

For agent-assisted user login, prefer the non-blocking device flow:

```bash
lark-cli auth login --recommend --no-wait
lark-cli auth login --device-code <DEVICE_CODE>
```

## Command Routing

### 1. Shortest Debug And Delivery Path

Use `chattool lark` only for:

- quick bot credential check: `chattool lark info`
- sending one simple text message: `chattool lark send`
- local prompt/session debugging in terminal: `chattool lark chat`

Do not move document, comment, permission, search, or reply workflows back into `chattool lark`.

### 2. Messages And Session Debugging

Use `lark-cli im` first:

- send: `lark-cli im +messages-send`
- reply: `lark-cli im +messages-reply`
- search chats / find `chat_id`: `lark-cli im +chat-search`
- list messages in a chat: `lark-cli im +chat-messages-list`
- inspect threads: `lark-cli im +threads-messages-list`

Core identifiers:

- `message_id`: one message; replies depend on this
- `chat_id`: one conversation or group chat
- `open_id`: one user object; usable for direct messages
- `receive_id_type`: tells the API what the target ID means

Heuristics:

- for a new send, first decide whether the real target is `chat_id` or `open_id`
- for a reply, think in `message_id`, not `chat_id`
- for the shortest delivery test, `chattool lark send` is fine
- for richer output and better debugging fields, prefer `lark-cli im +messages-send`

### 3. Document Body

Document body operations belong to `docs`:

- `lark-cli docs +create`
- `lark-cli docs +fetch`
- `lark-cli docs +update`

### 4. Comments And Permissions

Comments, comment replies, and permissions belong to `drive`:

- `lark-cli drive +add-comment`
- `lark-cli drive file.comment.replys create`
- `lark-cli drive file.comments list`
- `lark-cli drive file.comments patch`
- `lark-cli drive permission.members create`

### 5. Wiki Links

Resolve wiki links before treating them as doc tokens:

- `lark-cli wiki spaces get_node`

## Current Working Assumptions

These are consistent with the current repo docs and are safe defaults:

- try bot identity first for document body operations: `docs +create / +fetch / +update`
- try bot identity first for comments and basic sharing: `drive +add-comment`, `file.comment.replys create`, `permission.members create`
- search and discovery actions are more likely to require user identity
- do not build Markdown with literal `\n` in shell strings; prefer real newlines or heredoc
- comment listing may need a short retry right after creation

## Decision Rules

1. install or migrate config: `chattool setup lark-cli`
2. send one minimal text message: `chattool lark send`
3. reply, search, or inspect message/chat/thread state: `lark-cli im`
4. edit document body: `lark-cli docs`
5. comments, permission, comment replies: `lark-cli drive`
6. wiki resolution: `lark-cli wiki`

## What Matters Most

- choose the right command surface before writing commands
- do not design another parallel Feishu CLI
- when user login is needed in an agent session, prefer `--no-wait` + `--device-code`
- if parameter shape is unclear, check `--help` or `schema`
- prefer the shortest executable path over a broad explanation
