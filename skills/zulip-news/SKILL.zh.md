---
name: zulip-news
description: 通过 ChatTool CLI 聚合并总结 Zulip 社区动态。适用于获取最新 Zulip 更新、列出 stream/message，或基于已配置的 stream/topic 生成周期性摘要。
version: 0.1.0
---

# Zulip News

## 快速开始

1. 配置 Zulip 凭证和默认参数：
   `chattool chatenv cat -t zulip`
2. 列出 streams：
   `chattool zulip streams`
3. 生成摘要（控制台 + Markdown 文件）：
   `chattool zulip news --since-hours 24 --stream general --stream announcements`

## 核心 CLI

- `chattool zulip streams [--all] [--json-output]`
- `chattool zulip messages --stream <name> --before 20 [--topic <topic>] [--sender <email>]`
- `chattool zulip news [--since-hours N] [--per-stream N] [--limit N] [--output path]`

## 配置项

通过 `chatenv` 或 `.env` 设置默认值：

- `ZULIP_BOT_EMAIL`
- `ZULIP_BOT_API_KEY`
- `ZULIP_SITE`
- `ZULIP_NEWS_STREAMS`（逗号分隔的 stream 名称）
- `ZULIP_NEWS_TOPICS`（逗号分隔的 topic 名称）
- `ZULIP_NEWS_SINCE_HOURS`（默认 24）
- `ZULIP_NEWS_PER_STREAM`（默认 200）

## 说明

- `news` 默认在当前目录写出 `zulip-news-YYYYMMDD.md`，除非显式传入 `--output`
- 如果 LLM 摘要失败，会回退到规则式摘要
