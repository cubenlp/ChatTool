# test_chattool_lark_doc_markdown_task

任务导向地测试结构化 Markdown 文档链路，目标是验证“把本地 Markdown 转成 block JSON，再写进真实文档”。

## 元信息

- 命令：`chattool lark doc parse-md <path>`、`chattool lark doc append-json <document_id> <path>`
- 目的：定义结构化 docx 写入任务，覆盖 block JSON 生成与追加。
- 标签：`cli`
- 前置条件：具备飞书凭证、docx 写入权限与一篇可写文档。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_DEFAULT_RECEIVER_ID`
  - `FEISHU_TEST_USER_ID`（可选；仅在需要隔离测试用户时额外指定）
  - `FEISHU_TEST_USER_ID_TYPE`（可选；默认 `user_id`）
- 回滚：删除测试文档，或明确保留测试痕迹。

## 用例 1：把 Markdown 转成 block JSON

- 初始环境准备：
  - 准备一份包含标题、列表、引用和代码块的 `.md` 文件。
- 相关文件：
  - `<tmp>/doc.md`
  - `<tmp>/doc.blocks.json`

预期过程和结果：
  1. 执行 `chattool lark doc parse-md <path> -o <output>`。
  2. CLI 应生成 block JSON 文件。
  3. JSON 中应包含能反映标题、列表、引用、代码块的 block 结构。

参考执行脚本（伪代码）：

```sh
chattool lark doc parse-md /tmp/doc.md -o /tmp/doc.blocks.json
```

## 用例 2：把 block JSON 追加到真实文档

- 初始环境准备：
  - 准备一篇可写文档。
  - 准备一份符合 docx block 结构的 JSON 文件。
- 相关文件：
  - `<tmp>/doc.blocks.json`

预期过程和结果：
  1. 执行 `chattool lark doc append-json <document_id> <path>`。
  2. 终端应输出追加成功、block 数与 revision 信息。
  3. 文档侧应看到结构化内容被成功写入。

参考执行脚本（伪代码）：

```sh
chattool lark doc append-json doccnxxxxxxxxxxxx /tmp/doc.blocks.json
```
