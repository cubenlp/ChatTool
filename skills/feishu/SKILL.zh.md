---
name: feishu
description: 使用 `chattool lark` 作为唯一飞书入口。根 `SKILL.zh.md` 负责路由、能力地图和主题索引，具体资料全部下沉到子目录。
version: 0.4.0
---

# 飞书技能索引

这里只保留一个中文入口文件：`SKILL.zh.md`。安装时会整目录拷贝，因此其它资料全部按主题放到子目录中。

## 默认规则

- 先从 `chattool lark` 开始。
- 一次性业务输入优先走 CLI 参数，不新增临时环境变量。
- 若能力缺口具有复用价值，先补 `src/chattool/tools/lark/`。
- 测试与接口设计优先落到 `cli-tests/*.md`。

## 目录索引

- `guide/`
  - `overview.md` / `overview.zh.md`
    - 飞书总览与入口说明
  - `setup-and-routing.md`
    - 凭证、`-e/--env`、默认接收者、路由规则
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
- 飞书资料统一收口在这个目录与它的主题子目录中
- 先用 CLI，再按主题目录查资料
- 各主题文件都应围绕这一套 CLI/API 组织
- 默认用户优先使用 `FEISHU_DEFAULT_RECEIVER_ID`
- 只有在 CLI 真实测试需要隔离目标时，才额外使用 `FEISHU_TEST_USER_ID`

## 优先顺序

1. 先确认是否已有 `chattool lark` 命令可直接完成目标。
2. 如果已有，按对应主题目录查 CLI 用法和边界。
3. 如果 CLI 不足，先补目标命令面和 `cli-tests/*.md`。
4. 如果需要更深背景，继续在同一套主题文档和参考资料里补充。
