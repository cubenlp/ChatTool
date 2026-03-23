---
name: zulip-post-preview
description: 从 Zulip 读取指定主题，生成原文、翻译对照和中文导读的分阶段预览材料。
version: 0.1.0
---

# Zulip 帖子预览（中文）

目标：从 Zulip 读取指定主题，按阶段输出原文、翻译对照和中文导读。

## 只读原则

- 只使用 `chattool zulip` 的读取命令（`streams`/`topics`/`messages`/`topic`）。
- 不发送消息、不反应、不上传文件。

## 输出结构

目录：仓库外独立工作目录，例如 `~/tmp/chattool-zulip/<频道>/<主题>/`

阶段文件（命名约定）：
- `0_posts_full.md`：全量原文（按时间顺序）。
- `0_posts_5.zh-en.md`：首条 + 最新 5 条，原文与中文对照。
- `1_overview.md`：中文导读与摘要（1_ 开始均为加工内容，当前只做到 1_）。

## 操作流程

1. 找到 stream 与 topic  
   `chattool zulip streams`  
   `chattool zulip topics --stream "<stream name>"`

2. 拉取完整主题（只读）  
   `chattool zulip topic --stream "<stream name>" --topic "<topic name>" --json-output`

3. 生成 0_ 原文  
   - 按时间排序输出全部消息  
   - 每条消息包含时间、作者、链接与原始 markdown

4. 生成 0_ 翻译对照  
   - 只选首条 + 最新 5 条  
   - 每条包含原文与中文翻译

5. 生成 1_ 中文导读  
   - 提炼核心观点  
   - 指引先读哪部分再回到全量原文

## 复盘要点

- 目录层级保持 `频道/主题`，避免额外 raw 子目录。  
- 0_ 代表开始阶段（原文与对照），1_ 起全部中文加工。  
- 默认不要把这些预览产物直接写回仓库；只有明确需要长期保留时，再整理进正式目录。  
- 内容只读，避免任何写入到 Zulip 端的行为。
