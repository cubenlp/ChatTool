# test_chattool_lark_doc_create_notify_task

任务导向地测试文档创建与通知链路，目标是验证“创建一篇真实飞书文档并把链接发给默认用户”。

## 元信息

- 命令：`chattool lark doc create <title>`、`chattool lark notify-doc <title> [text]`
- 目的：定义文档创建与通知任务，作为后续读取、追加和更新任务的起点。
- 标签：`cli`
- 前置条件：具备飞书凭证、docx 创建权限与默认接收者。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_DEFAULT_RECEIVER_ID`
  - `FEISHU_TEST_USER_ID`（可选；仅在需要隔离测试用户时额外指定）
  - `FEISHU_TEST_USER_ID_TYPE`（可选；默认 `user_id`）
- 回滚：删除测试文档；如发送了通知消息，视需要手动清理消息。

## 用例 1：创建一篇空文档

- 初始环境准备：
  - 飞书凭证可用，应用具备文档创建权限。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark doc create "唯一标题的测试文档"`。
  2. 终端应输出 `document_id` 与标题。
  3. 飞书侧应实际创建出该文档。

参考执行脚本（伪代码）：

```sh
chattool lark doc create "cli task: create doc $(date +%s)"
```

## 用例 2：创建文档并通知默认用户

- 初始环境准备：
  - 已配置 `FEISHU_DEFAULT_RECEIVER_ID`。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark notify-doc "唯一标题" "一段唯一正文"`。
  2. CLI 应创建文档、追加正文并取回链接。
  3. 终端应输出通知消息 `message_id`、`document_id` 与 URL。
  4. 默认用户应收到带文档链接的通知消息。

参考执行脚本（伪代码）：

```sh
chattool lark notify-doc "cli task: notify doc $(date +%s)" "seed text"
```
