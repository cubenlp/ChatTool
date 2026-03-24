---
name: feishu
description: Use `chattool lark` as the single Feishu entry. This root index routes work into topic folders, keeps archive coverage, and points to the right CLI surface first.
version: 0.4.0
---

# Feishu Skill Index

这里只保留一个入口文件：`SKILL.md`。安装时会整目录拷贝，因此其它资料全部按主题放到子目录里。

## 默认规则

- 先从 `chattool lark` 开始。
- 业务输入优先走 CLI 参数，不新增临时环境变量。
- 若能力缺口具有复用价值，先补 `src/chattool/tools/lark/`。
- 测试与接口设计优先落到 `cli-tests/*.md`。

## 目录索引

- `guide/`
  - `overview.md` / `overview.zh.md`
    - 旧主 skill 内容归档版，对照当前 CLI 使用
  - `setup-and-routing.md`
    - 凭证、`-e/--env`、默认接收者、测试用户、路由规则
  - `api-reference.md`
    - 官方 API 文档 URL 与 CLI 对应
- `messaging/`
  - `messaging.md`
  - `channel-rules.md`
  - `lark-markdown-syntax.md`
  - `im-read.md`
  - `troubleshoot.md`
- `documents/`
  - `documents.md`
  - `create-doc.md`
  - `fetch-doc.md`
  - `update-doc.md`
  - `official-docx-capabilities.md`
  - `feishu-docx-adoption-notes.md`
- `calendar/`
  - `calendar.md`
- `task/`
  - `task.md`
- `bitable/`
  - `bitable.md`
  - `references/examples.md`
  - `references/field-properties.md`
  - `references/record-values.md`

## 路由规则

- 现在只有一个飞书 skill 目录：`skills/feishu/`
- 不再把任务路由到 `feishu-*` 同级 skill
- 先用 CLI，再按主题目录查资料
- 各主题文件都保留了 archive 基础内容，并补了当前 CLI 用法说明

## 优先顺序

1. 先确认是否已有 `chattool lark` 命令可直接完成目标。
2. 如果已有，按对应主题目录查 CLI 用法和边界。
3. 如果 CLI 不足，先补目标命令面和 `cli-tests/*.md`。
4. 如果需要更深背景，再看保留的 archive 基础内容和参考资料。
