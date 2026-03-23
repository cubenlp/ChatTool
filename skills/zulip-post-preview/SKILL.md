---
name: zulip-post-preview
description: Create staged previews of Zulip topics using read-only CLI queries, including full-thread originals, a small zh-en translation slice, and a Chinese overview in an external work directory such as ~/tmp/chattool-zulip/<channel>/<topic>. Use when asked to preview, summarize, or translate Zulip thread content.
version: 0.1.0
---

# Zulip Post Preview

## Overview

Generate a staged readlist for a Zulip topic using only read-only CLI commands and write results to an external work directory outside the repository.

## Workflow

1. Identify stream and topic  
   Use `chattool zulip streams` and `chattool zulip topics --stream "<stream name>"`.

2. Fetch full topic (read-only)  
   Use `chattool zulip topic --stream "<stream name>" --topic "<topic name>" --json-output`.

3. Produce staged outputs under `~/tmp/chattool-zulip/<channel>/<topic>/`  
   - `0_posts_full.md`: full thread, chronological, original markdown with timestamp, sender, and link.  
   - `0_posts_5.zh-en.md`: first post + latest 5 posts, original text with Chinese translation.  
   - `1_overview.md`: Chinese summary and reading guidance (1_ and later are processed content; stop at 1_ for now).

## Read-only Rules

Use only read methods (`streams`, `topics`, `messages`, `topic`). Do not send messages, react, or upload files.

## Review Notes

Keep the directory structure flat (`<channel>/<topic>`), avoid extra `raw/` folders, and do not write temporary preview outputs back into the repository by default.
