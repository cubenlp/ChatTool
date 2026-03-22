---
name: feishu
description: Use `chattool lark` as the primary entry for Feishu/Lark verification, messaging, document workflows, and local debugging. Prefer CLI parameters for business inputs and extend ChatTool before writing ad-hoc scripts.
---

# Feishu Skill

Use `chattool lark` first. Do not start with raw OpenAPI scripts when the CLI already covers the task.

## Goal

- Verify bot credentials and scopes.
- Send messages, files, cards, and replies.
- Create Feishu docs, append local text or markdown files, and send doc links.
- Debug listen/chat flows locally.

## Routing Rules

1. Prefer `chattool lark` for all normal Feishu work.
2. Put business inputs in CLI args, not extra env vars.
3. If a capability is missing and reusable, extend `src/chattool/tools/lark/` first.
4. Keep skill docs task-oriented and move detailed procedures into topic files.

## Core Commands

```bash
chattool lark info
chattool lark scopes -f im
chattool lark send <receiver> "hello"
chattool lark reply <message_id> "done"
chattool lark doc create "Weekly Notes"
chattool lark doc append-file <document_id> ./notes.md
chattool lark notify-doc "Weekly Notes" --append-file ./notes.md
chattool lark listen -l DEBUG
chattool lark chat --system "You are a Feishu assistant"
```

## Topic Docs

- `docs/setup-and-routing.md`: credential setup, env usage, routing rules.
- `docs/messaging.md`: send/upload/reply/listen/chat flows.
- `docs/documents.md`: doc create/get/raw/blocks/append-text/append-file/notify-doc.

## Notes

- `FEISHU_APP_ID` and `FEISHU_APP_SECRET` stay in config only.
- `FEISHU_DEFAULT_RECEIVER_ID` is optional and only for default delivery.
- For `.md` inputs, ChatTool converts markdown into Feishu-compatible plain-text paragraphs before appending.
