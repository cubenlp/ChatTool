---
name: zulip-news
description: Aggregate and summarize Zulip community updates via ChatTool CLI. Use for latest Zulip news, stream/topic listing, and periodic summaries from configured streams/topics.
version: 0.1.1
---

# Zulip News

Use this skill to collect and summarize Zulip messages with ChatTool.

## Configuration

Configure Zulip credentials with typed env:

```bash
chatenv init -t zulip
chatenv cat -t zulip
```

Typical keys include bot email, bot API key, site URL, default streams/topics, lookback hours, and per-stream fetch limit.

## Common Commands

```bash
chattool zulip streams
chattool zulip messages --stream "general" --topic "announcements"
chattool zulip news
chattool zulip news --since-hours 24
```

Use configured defaults when the user asks for periodic or latest community updates. Ask for stream/topic only when neither the request nor the typed env defaults provide enough scope.

## Output Guidance

- Summarize newest and most actionable updates first.
- Group by stream/topic when multiple sources are involved.
- Include message links or ids when available.
- Do not expose API keys or raw credential values.
