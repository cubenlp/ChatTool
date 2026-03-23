# test_chattool_lark_doc_markdown

测试 `chattool lark doc parse-md`、`append-file` 与 `notify-doc --append-file` 的 Markdown 链路，覆盖结构化 block 生成、段落提取与稳态追加。

## 元信息

- 命令：`chattool lark doc parse-md <path>`、`chattool lark doc append-json <document_id> <path>`、`chattool lark doc append-file <document_id> <path>`、`chattool lark notify-doc <title> --append-file <path>`
- 目的：验证 Markdown 文件可先转换为飞书 docx block JSON，并继续用于文档写入。
- 标签：`cli`
- 前置条件：具备飞书凭证与文档写入权限。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_DEFAULT_RECEIVER_ID`
  - `FEISHU_TEST_USER_ID`
  - `FEISHU_TEST_USER_ID_TYPE`
- 回滚：删除测试文档或测试块（如适用）。

## 用例 1：将 Markdown 文件转换为 block JSON

- 初始环境准备：
  - 准备一份包含标题、列表、引用和代码块的 `.md` 文件。
- 相关文件：
  - `<tmp>/doc.md`

预期过程和结果：
  1. 执行 `chattool lark doc parse-md <path>`。
  2. 预期输出 JSON 数组。
  3. 预期标题、列表、引用、代码块映射为对应的飞书 block 类型。

参考执行脚本（伪代码）：

```sh
chattool lark doc parse-md /tmp/doc.md
```

## 用例 2：将 block JSON 追加到已有文档

- 初始环境准备：
  - 准备一个可写的 `document_id`。
  - 准备一份符合飞书 docx block 结构的 `.json` 文件。
- 相关文件：
  - `<tmp>/blocks.json`

预期过程和结果：
  1. 执行 `chattool lark doc append-json <document_id> <path>`。
  2. 预期 CLI 输出 JSON 追加成功、block 数与 revision 信息。
  3. 预期文档写入直接消费结构化 block，而不是重新走纯文本段落转换。

参考执行脚本（伪代码）：

```sh
chattool lark doc append-json doccnxxxxxxxxxxxx /tmp/blocks.json
```

## 用例 3：将 Markdown 文件追加到已有文档

- 初始环境准备：
  - 准备一个可写的 `document_id`。
  - 准备一份包含标题、列表、链接和代码块的 `.md` 文件。
- 相关文件：
  - `<tmp>/doc.md`

预期过程和结果：
  1. 执行 `chattool lark doc append-file <document_id> <path>`。
  2. 预期 CLI 输出文件追加成功、段落数与 revision 信息。
  3. 预期 Markdown 被整理为飞书兼容的纯文本段落，而不是原样整块提交。

参考执行脚本（伪代码）：

```sh
chattool lark doc append-file doccnxxxxxxxxxxxx /tmp/doc.md
```

## 用例 4：创建文档并从 Markdown 文件追加正文后通知

- 初始环境准备：
  - 配置 `FEISHU_DEFAULT_RECEIVER_ID` 或显式传入 `--receiver`。
  - 准备一份 Markdown 文件。
- 相关文件：
  - `<tmp>/notify.md`

预期过程和结果：
  1. 执行 `chattool lark notify-doc "周报" --append-file <path>`。
  2. 预期创建文档成功。
  3. 预期正文由 Markdown 转成多段纯文本写入。
  4. 预期文档链接被发送给目标接收者。

参考执行脚本（伪代码）：

```sh
chattool lark notify-doc "周报" --append-file /tmp/notify.md
```
