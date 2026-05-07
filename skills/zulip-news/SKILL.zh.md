---
name: zulip-news
description: 通过 ChatTool CLI 聚合和总结 Zulip 社区更新。适用于获取最新 Zulip 消息、列出 stream/topic，或基于配置生成周期总结。
version: 0.1.1
---

# Zulip News

使用这个 skill 通过 ChatTool 收集和总结 Zulip 消息。

## 配置

使用 typed env 配置 Zulip 凭证：

```bash
chatenv init -t zulip
chatenv cat -t zulip
```

常见配置包括 bot email、bot API key、site URL、默认 streams/topics、回溯小时数和单 stream 拉取上限。

## 常用命令

```bash
chattool zulip streams
chattool zulip messages --stream "general" --topic "announcements"
chattool zulip news
chattool zulip news --since-hours 24
```

当用户要求周期更新或最新社区动态时，优先使用已配置默认值。只有请求和 typed env 默认值都不足以确定范围时，才询问 stream/topic。

## 输出要求

- 最新、最可行动的信息优先。
- 多来源时按 stream/topic 分组。
- 可用时附 message link 或 id。
- 不暴露 API key 或原始凭证值。
