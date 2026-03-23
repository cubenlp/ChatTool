---
name: feishu
description: Use `chattool lark` as the primary entry for Feishu verification, messaging, document workflows, and local debugging. Treat this skill as the Feishu index: route tasks to CLI first, then topic docs, then reusable CLI/tooling changes.
version: 0.2.0
---

# Feishu Skill

This skill is the Feishu entry index. `SKILL.md` only routes work; the whole `skills/feishu/` directory is installed together, so use the bundled docs as the working package.

## Default Rule

- Start with `chattool lark`.
- Put business inputs in CLI arguments, not temporary env vars.
- If the capability is reusable and missing, extend `src/chattool/tools/lark/` first.
- Keep this skill package focused on routing, reference, and execution guidance.

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
- Local debugging
  - `chattool lark listen`
  - `chattool lark chat`

## Topic Docs

- `docs/setup-and-routing.md`
  - credentials, `-e/--env`, default receiver, test-user config, routing rules
- `docs/messaging.md`
  - send/upload/reply/listen/chat workflows
- `docs/documents.md`
  - document commands, stable text track, structured docx track
- `docs/api-reference.md`
  - official API doc URLs and CLI-to-API mapping
- `docs/official-docx-capabilities.md`
  - docx block boundaries and current implementation scope
- `docs/feishu-docx-adoption-notes.md`
  - what to borrow from external references and what not to import directly

## Independent Skills

- `feishu-bitable`
- `feishu-calendar`
- `feishu-im-read`
- `feishu-task`
- `feishu-troubleshoot`
- `feishu-channel-rules`

Document-only legacy skills are intentionally folded back into this package. Use the docs above instead of separate create/fetch/update doc skills.

## Implementation Priority

1. Reuse an existing `chattool lark` command when it already covers the task.
2. If the CLI is missing a reusable Feishu action, add or refine the CLI/tooling first.
3. Only after the command shape is clear, update this skill package and topic docs.
4. When extending beyond current coverage, start from `docs/api-reference.md` and official Feishu docs, then codify the result back into ChatTool.
