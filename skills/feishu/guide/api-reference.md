# 飞书 API Reference

这份文档只保留实用索引，用于继续扩 `chattool lark` 时查官方文档，不搬运整段官方原文。

## 当前 CLI 与 API 对应

### 机器人与权限

- `chattool lark info`
  - Bot info: <https://open.feishu.cn/document/server-docs/bot-v3/bot/get>
- `chattool lark scopes`
  - App scopes: <https://open.feishu.cn/document/server-docs/application-v6/app-permission/list>

### 消息

- `chattool lark send`
  - Send message: <https://open.feishu.cn/document/server-docs/im-v1/message/create>
- `chattool lark reply`
  - Reply message: <https://open.feishu.cn/document/server-docs/im-v1/message/reply>
- `chattool lark upload`
  - Upload image: <https://open.feishu.cn/document/server-docs/im-v1/image/create>
  - Upload file: <https://open.feishu.cn/document/server-docs/im-v1/file/create>

### 文档

- `chattool lark notify-doc`
- `chattool lark doc create|get|raw|blocks|append-text|append-file|parse-md|append-json`
- `chattool lark doc perm-public-get|perm-public-set`
- `chattool lark doc perm-member-list|perm-member-add`
  - Docx document: <https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/create>
  - Docx raw content: <https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/raw_content>
  - Docx block children: <https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block-children/list>
  - Append block children: <https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block-children/create>
  - Drive meta batch query: <https://open.feishu.cn/document/server-docs/docs/drive-v1/meta/batch_query>
  - Public permission get: <https://open.feishu.cn/document/server-docs/docs/drive-v1/permission-public/get>
  - Public permission patch: <https://open.feishu.cn/document/server-docs/docs/drive-v1/permission-public/patch>
  - Permission member list: <https://open.feishu.cn/document/server-docs/docs/drive-v1/permission-member/list>
  - Permission member create: <https://open.feishu.cn/document/server-docs/docs/drive-v1/permission-member/create>

### 后续专题 CLI

- `chattool lark bitable ...`
  - Bitable overview: <https://open.feishu.cn/document/server-docs/docs/bitable-v1/bitable-overview>
- `chattool lark calendar ...`
  - Calendar overview: <https://open.feishu.cn/document/server-docs/calendar-v4/intro>
- `chattool lark im ...`
  - IM message list/search/resource: <https://open.feishu.cn/document/server-docs/im-v1/introduction>
- `chattool lark task ...`
  - Task overview: <https://open.feishu.cn/document/server-docs/task-v2/introduction>

## 使用规则

- 先定 CLI 目标命令，再查对应 API。
- 不把 API 资源名直接搬成用户命令名。
- 继续扩结构化文档能力前，先看 `../documents/official-docx-capabilities.md`。
