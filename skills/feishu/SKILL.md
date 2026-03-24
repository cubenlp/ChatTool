---
name: feishu
description: Use `chattool lark` as the single Feishu entry. This root index routes work into topic folders and points to the one supported CLI/API surface.
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

## Skill 与 CLI Tests 对应

- `SKILL.md`
  - `cli-tests/lark/guide/test_chattool_lark_skill_index.md`
- `guide/overview.md`
  - `cli-tests/lark/guide/test_chattool_lark_overview.md`
- `guide/overview.zh.md`
  - `cli-tests/lark/guide/test_chattool_lark_overview_zh.md`
- `guide/setup-and-routing.md`
  - `cli-tests/lark/guide/test_chattool_lark_setup_and_routing.md`
- `guide/api-reference.md`
  - `cli-tests/lark/guide/test_chattool_lark_api_reference.md`
- `messaging/messaging.md`
  - `cli-tests/lark/messaging/test_chattool_lark_send_text_task.md`
  - `cli-tests/lark/messaging/test_chattool_lark_send_file_task.md`
  - `cli-tests/lark/messaging/test_chattool_lark_send_card_task.md`
  - `cli-tests/lark/messaging/test_chattool_lark_reply_task.md`
  - `cli-tests/lark/messaging/test_chattool_lark_listen_task.md`
- `messaging/channel-rules.md`
  - `cli-tests/lark/messaging/test_chattool_lark_channel_rules.md`
- `messaging/lark-markdown-syntax.md`
  - `cli-tests/lark/messaging/test_chattool_lark_markdown_syntax.md`
- `messaging/im-read.md`
  - `cli-tests/lark/im/test_chattool_lark_im_basic.md`
  - `cli-tests/lark/im/test_chattool_lark_im_list_task.md`
- `messaging/troubleshoot.md`
  - `cli-tests/lark/troubleshoot/test_chattool_lark_troubleshoot_basic.md`
  - `cli-tests/lark/troubleshoot/test_chattool_lark_troubleshoot_message_task.md`
- `documents/documents.md`
  - `cli-tests/lark/documents/test_chattool_lark_doc_basic.md`
  - `cli-tests/lark/documents/test_chattool_lark_doc_markdown.md`
- `documents/create-doc.md`
  - `cli-tests/lark/documents/test_chattool_lark_doc_create_notify_task.md`
- `documents/fetch-doc.md`
  - `cli-tests/lark/documents/test_chattool_lark_doc_fetch_task.md`
- `documents/update-doc.md`
  - `cli-tests/lark/documents/test_chattool_lark_doc_update_task.md`
- `documents/official-docx-capabilities.md`
  - `cli-tests/lark/documents/test_chattool_lark_docx_capabilities.md`
- `documents/feishu-docx-adoption-notes.md`
  - `cli-tests/lark/documents/test_chattool_lark_docx_adoption.md`
- `calendar/calendar.md`
  - `cli-tests/lark/calendar/test_chattool_lark_calendar_basic.md`
- `task/task.md`
  - `cli-tests/lark/task/test_chattool_lark_task_basic.md`
- `bitable/bitable.md`
  - `cli-tests/lark/bitable/test_chattool_lark_bitable_basic.md`
- `bitable/references/examples.md`
  - `cli-tests/lark/bitable/test_chattool_lark_bitable_examples.md`
- `bitable/references/field-properties.md`
  - `cli-tests/lark/bitable/test_chattool_lark_bitable_field_properties.md`
- `bitable/references/record-values.md`
  - `cli-tests/lark/bitable/test_chattool_lark_bitable_record_values.md`

## 路由规则

- 现在只有一个飞书 skill 目录：`skills/feishu/`
- 不再把任务路由到 `feishu-*` 同级 skill
- 先用 CLI，再按主题目录查资料
- 各主题文件都应围绕这一套 CLI/API 组织
- 默认用户优先使用 `FEISHU_DEFAULT_RECEIVER_ID`
- 只有在 CLI 真实测试需要隔离目标时，才额外使用 `FEISHU_TEST_USER_ID`

## 优先顺序

1. 先确认是否已有 `chattool lark` 命令可直接完成目标。
2. 如果已有，按对应主题目录查 CLI 用法和边界。
3. 如果 CLI 不足，先补目标命令面和 `cli-tests/*.md`。
4. 如果需要更深背景，继续在同一套主题文档和参考资料里补充。
