---
name: zulip-post-preview
description: "Fetch, stage, and translate Zulip thread content into structured markdown files. Use when the user asks to preview, summarize, translate, or read a Zulip topic, channel thread, or message stream."
version: 0.1.0
---

# Zulip Post Preview

Generate a staged readlist for a Zulip topic using read-only CLI commands and write results to an external work directory outside the repository.

## Workflow

1. **Identify stream and topic**
   - List streams: `chattool zulip streams`
   - List topics: `chattool zulip topics --stream "<stream name>"`

2. **Fetch full topic (read-only)**
   ```bash
   chattool zulip topic --stream "<stream name>" --topic "<topic name>" --json-output
   ```

3. **Write staged outputs** under `~/tmp/chattool-zulip/<channel>/<topic>/`
   - `0_posts_full.md`: full thread, chronological, original markdown with timestamp, sender, and link.
   - `0_posts_5.zh-en.md`: first post + latest 5 posts, original text with Chinese translation.
   - `1_overview.md`: Chinese summary and reading guidance.

## Read-only Rules

Use only read methods: `streams`, `topics`, `messages`, `topic`. Do not send messages, react, or upload files.

## Output Structure Rules

- Keep directory structure flat: `<channel>/<topic>/` — no extra `raw/` subfolders.
- Do not write preview outputs back into the repository.
- Stop at `1_overview.md` unless further processing is explicitly requested.
