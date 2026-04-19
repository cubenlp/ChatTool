---
name: zulip-post-preview
description: "抓取、整理并翻译 Zulip 话题内容，输出结构化 markdown 预览文件。用户提到预览、总结、翻译或阅读某个 Zulip topic、频道线程或消息流时使用。"
version: 0.1.0
---

# Zulip Post Preview

使用只读 CLI 命令生成某个 Zulip topic 的分阶段阅读材料，并把结果写到仓库外部的工作目录。

## 工作流

1. **确定 stream 和 topic**
   - `chattool zulip streams`
   - `chattool zulip topics --stream "<stream name>"`

2. **只读拉取完整主题**
   ```bash
   chattool zulip topic --stream "<stream name>" --topic "<topic name>" --json-output
   ```

3. **写入分阶段文件** 到 `~/tmp/chattool-zulip/<channel>/<topic>/`
   - `0_posts_full.md`：完整原文，按时间顺序，包含时间、发送者和链接
   - `0_posts_5.zh-en.md`：首条 + 最新 5 条，中英对照
   - `1_overview.md`：中文摘要与阅读建议

## 只读规则

只使用读取命令：`streams`、`topics`、`messages`、`topic`。不要发送消息、加表情或上传文件。

## 输出结构规则

- 目录保持扁平：`<channel>/<topic>/`，不要额外加 `raw/` 子目录
- 预览文件默认不要写回仓库
- 除非用户明确要求继续加工，否则停在 `1_overview.md`
