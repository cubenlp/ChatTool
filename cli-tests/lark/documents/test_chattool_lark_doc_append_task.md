# test_chattool_lark_doc_append_task

任务导向地测试文档追加链路，目标是验证“向一篇真实文档稳定追加文本或本地 Markdown 文件”。

## 元信息

- 命令：`chattool lark doc append-text <document_id> <text>`、`chattool lark doc append-file <document_id> <path>`
- 目的：定义文档稳态追加任务，覆盖正文文本和本地文件两条主线。
- 标签：`cli`
- 前置条件：具备飞书凭证、docx 写入权限与一篇可写文档。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_DEFAULT_RECEIVER_ID`
  - `FEISHU_TEST_USER_ID`（可选；仅在需要隔离测试用户时额外指定）
  - `FEISHU_TEST_USER_ID_TYPE`（可选；默认 `user_id`）
- 回滚：删除测试文档，或明确保留测试痕迹。

## 用例 1：向文档追加一段纯文本

- 初始环境准备：
  - 准备一篇可写文档。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark doc append-text <document_id> "唯一追加文本"`。
  2. 终端应输出追加成功与 revision 信息。
  3. 重新执行 `doc raw` 时，应能在文档内容中看到这段唯一文本。

参考执行脚本（伪代码）：

```sh
chattool lark doc append-text doccnxxxxxxxxxxxx "cli task append $(date +%s)"
```

## 用例 2：从 Markdown 文件追加正文

- 初始环境准备：
  - 准备一篇可写文档。
  - 准备一份包含标题、列表和链接的 `.md` 文件。
- 相关文件：
  - `<tmp>/append.md`

预期过程和结果：
  1. 执行 `chattool lark doc append-file <document_id> <path>`。
  2. 终端应输出追加成功、段落数与 revision 信息。
  3. Markdown 内容应被整理成飞书兼容的段落，而不是原样整块提交。

参考执行脚本（伪代码）：

```sh
chattool lark doc append-file doccnxxxxxxxxxxxx /tmp/chattool-doc-append.md
```
