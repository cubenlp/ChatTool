---
name: feishu
description: "Send messages, manage documents, and interact with Feishu/Lark using lark-cli and chattool. Use when the user asks to send a Feishu message, reply to a thread, create or edit a Lark doc, resolve a wiki link, manage permissions, or debug Feishu bot credentials."
version: 1.0.0
---

# Feishu Skill

Interact with Feishu/Lark for messaging, documents, wiki, and permissions using `lark-cli` as the primary tool and `chattool lark` for quick debug and delivery.

Chinese version: `skills/feishu/SKILL.zh.md`

## Command Routing (Decision Rules)

| Task | Command |
| :--- | :--- |
| Install or migrate config | `chattool setup lark-cli` |
| Quick bot credential check | `chattool lark info` |
| Send one simple text message | `chattool lark send` |
| Local prompt/session debug | `chattool lark chat` |
| Send rich message, reply, search chats | `lark-cli im` |
| Create, fetch, or update document body | `lark-cli docs` |
| Add comments, manage permissions | `lark-cli drive` |
| Resolve wiki links | `lark-cli wiki spaces get_node` |

**Do not** build parallel Feishu CLI logic inside ChatTool. `chattool lark` covers only `info`, `send`, and `chat`.

## Workflow

1. **Classify the task**: config, messaging, documents, wiki, or permissions.
2. **Start from `lark-cli`** by default.
3. **Use `--dry-run`** first for write operations.
4. **Switch to user login** only when bot identity is insufficient.

### Auth Setup
```bash
chattool setup lark-cli
lark-cli auth status
lark-cli auth login --recommend
```

For agent-assisted login (non-blocking):
```bash
lark-cli auth login --recommend --no-wait
lark-cli auth login --device-code <DEVICE_CODE>
```

## Messaging (`lark-cli im`)

```bash
lark-cli im +messages-send
lark-cli im +messages-reply
lark-cli im +chat-search          # find chat_id
lark-cli im +chat-messages-list
lark-cli im +threads-messages-list
```

**ID heuristics**:
- New send: decide between `chat_id` (group) and `open_id` (user DM) first.
- Reply: work from `message_id`, not `chat_id`.
- Quick delivery test: `chattool lark send` is sufficient.

## Documents (`lark-cli docs`)

```bash
lark-cli docs +create
lark-cli docs +fetch
lark-cli docs +update
```

## Comments and Permissions (`lark-cli drive`)

```bash
lark-cli drive +add-comment
lark-cli drive file.comment.replys create
lark-cli drive file.comments list
lark-cli drive file.comments patch
lark-cli drive permission.members create
```

## Key References

- `docs/blog/agent-cli/lark-cli-guide.md`
- `docs/blog/agent-cli/feishu-cli-doc-practice.md`
- `docs/blog/lark-message-session-debug.md`
- `docs/tools/lark/index.md`
- `lark-cli/`

## Working Assumptions

- Bot identity works for document body ops (`docs +create / +fetch / +update`) and basic sharing.
- Search and discovery actions are more likely to require user identity.
- Do not build Markdown with literal `\n` in shell strings — use real newlines or heredoc.
- Comment listing may need a short retry immediately after creation.
