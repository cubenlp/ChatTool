---
name: feishu
description: Use `chattool lark` as the single Feishu CLI entry. This skill is the Feishu index: route work to CLI first, then the topic markdown files in this directory, then back into reusable CLI development.
version: 0.3.0
---

# Feishu Skill

This skill is the single Feishu entry index. `SKILL.md` only routes work; the whole `skills/feishu/` directory is installed together, so treat the markdown files in this directory as one working package.

## Default Rule

- Start with `chattool lark`.
- Put business inputs in CLI arguments, not temporary env vars.
- If the capability is reusable and missing, extend `src/chattool/tools/lark/` first.
- Keep this skill package focused on CLI routing, test-first design, and execution guidance.

## Capability Map

- Verification and permission checks
  - `chattool lark info`
  - `chattool lark scopes`
- Messaging and resource delivery
  - `chattool lark send`
  - `chattool lark upload`
  - `chattool lark reply`
- Document workflows
  - Stable text track: `chattool lark notify-doc`, `doc append-text`, `doc append-file`
  - Structured docx track: `chattool lark doc parse-md`, `doc append-json`
- Planned topic groups
  - `chattool lark bitable ...`
  - `chattool lark calendar ...`
  - `chattool lark im ...`
  - `chattool lark task ...`
  - `chattool lark troubleshoot ...`
- Local debugging
  - `chattool lark listen`
  - `chattool lark chat`

## Topic Docs

- `setup-and-routing.md`
  - credentials, `-e/--env`, default receiver, test-user config, routing rules
- `messaging.md`
  - send/upload/reply/listen/chat workflows
- `documents.md`
  - document commands, stable text track, structured docx track
- `bitable.md`
  - target `chattool lark bitable ...` command surface and test-first scenarios
- `calendar.md`
  - target `chattool lark calendar ...` command surface and test-first scenarios
- `im-read.md`
  - target `chattool lark im ...` command surface and real-message reading workflows
- `task.md`
  - target `chattool lark task ...` command surface and task/tasklist flows
- `troubleshoot.md`
  - target `chattool lark troubleshoot ...` command surface and diagnostics workflow
- `channel-rules.md`
  - Feishu output constraints for `send`, `reply`, cards, posts, and docs
- `api-reference.md`
  - official API doc URLs and CLI-to-API mapping
- `official-docx-capabilities.md`
  - docx block boundaries and current implementation scope
- `feishu-docx-adoption-notes.md`
  - what to borrow from external references and what not to import directly
- `bitable-field-properties.md`
  - reference for field property structures during CLI extension
- `bitable-record-values.md`
  - reference for record payload formats during CLI extension
- `bitable-examples.md`
  - scenario examples for future `chattool lark bitable ...` work
- `lark-markdown-syntax.md`
  - Feishu markdown and card syntax constraints

## Routing Rule

There is only one Feishu skill directory now: `skills/feishu/`.

- Do not route to `feishu-*` sibling skill directories.
- Use the topic markdown files in this directory instead.
- If a topic is not implemented in CLI yet, write the target command surface and `cli-tests/*.md` first.

## Implementation Priority

1. Reuse an existing `chattool lark` command when it already covers the task.
2. If the CLI is missing a reusable Feishu action, define the target command and `cli-tests/*.md` first.
3. Only after the command shape is clear, add or refine the CLI/tooling implementation.
4. When extending beyond current coverage, start from `api-reference.md` and official Feishu docs, then codify the result back into ChatTool.
