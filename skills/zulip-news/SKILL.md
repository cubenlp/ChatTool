---
name: zulip-news
description: "Aggregate and summarize Zulip community updates via ChatTool CLI. Use when user asks to fetch latest Zulip news, list streams/messages, or generate periodic summaries from configured streams/topics."
version: 0.1.0
---

# Zulip News

## Quick Start

1. Configure Zulip credentials and defaults:
   `chattool chatenv cat -t zulip`
2. List streams:
   `chattool zulip streams`
3. Generate a summary (console + Markdown file):
   `chattool zulip news --since-hours 24 --stream general --stream announcements`

## Core CLI

- `chattool zulip streams [--all] [--json-output]`
- `chattool zulip messages --stream <name> --before 20 [--topic <topic>] [--sender <email>]`
- `chattool zulip news [--since-hours N] [--per-stream N] [--limit N] [--output path]`

## Configuration

Set defaults via `chatenv` or `.env`:

- `ZULIP_BOT_EMAIL`
- `ZULIP_BOT_API_KEY`
- `ZULIP_SITE`
- `ZULIP_NEWS_STREAMS` (comma-separated stream names)
- `ZULIP_NEWS_TOPICS` (comma-separated topic names)
- `ZULIP_NEWS_SINCE_HOURS` (default 24)
- `ZULIP_NEWS_PER_STREAM` (default 200)

## Notes

- `news` writes `zulip-news-YYYYMMDD.md` in the current directory unless `--output` is provided.
- If LLM summarization fails, it falls back to a rule-based summary.
