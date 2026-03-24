# test_chattool_lark_doc_update_task

任务导向地定义 `chattool lark doc update ...` 的第一阶段目标，目标是验证“对真实文档做局部更新，而不是整篇重写”。

## 元信息

- 命令：`chattool lark doc update <document_id> --mode <mode> ...`
- 目的：先固定文档高级更新 CLI 的任务场景与验收方式，再补实现。
- 标签：`cli`
- 前置条件：具备飞书凭证、docx 写入权限与一篇结构清晰的测试文档。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_DEFAULT_RECEIVER_ID`
  - `FEISHU_TEST_USER_ID`（可选；仅在需要隔离测试用户时额外指定）
  - `FEISHU_TEST_USER_ID_TYPE`（可选；默认 `user_id`）
- 回滚：删除测试文档，或在结束时把文档恢复到初始内容。

## 第一阶段命令面

```sh
chattool lark doc update <document_id> --mode replace-range --selection-by-title "## 章节" --markdown "<新内容>"
chattool lark doc update <document_id> --mode insert-after --selection-by-title "## 章节" --markdown "<补充内容>"
chattool lark doc update <document_id> --mode delete-range --selection-by-title "## 章节"
chattool lark doc update <document_id> --mode replace-range --selection-with-ellipsis "开头...结尾" --markdown "<新内容>"
```

## 用例 1：按标题替换整段章节

- 初始环境准备：
  - 准备一篇包含 `## 功能说明` 标题的测试文档。
- 相关文件：
  - `<tmp>/replace.md`

预期过程和结果：
  1. 执行 `doc update --mode replace-range --selection-by-title "## 功能说明"`。
  2. CLI 应只替换该标题及其章节内容，而不是重写整个文档。
  3. 重新执行 `doc raw` 时，应看到新章节内容已经生效。

参考执行脚本（伪代码）：

```sh
chattool lark doc update doccnxxxxxxxxxxxx \
  --mode replace-range \
  --selection-by-title "## 功能说明" \
  --markdown "$(cat /tmp/replace.md)"
```

## 用例 2：按标题删除整段章节

- 初始环境准备：
  - 准备一篇包含 `## 废弃章节` 的测试文档。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `doc update --mode delete-range --selection-by-title "## 废弃章节"`。
  2. CLI 应只删除对应章节，不影响其它章节。
  3. 重新执行 `doc raw` 时，不应再看到该章节标题与正文。

参考执行脚本（伪代码）：

```sh
chattool lark doc update doccnxxxxxxxxxxxx \
  --mode delete-range \
  --selection-by-title "## 废弃章节"
```

## 用例 3：按内容范围插入补充说明

- 初始环境准备：
  - 准备一篇包含稳定文本锚点的测试文档。
- 相关文件：
  - `<tmp>/insert.md`

预期过程和结果：
  1. 执行 `doc update --mode insert-after --selection-with-ellipsis "开头...结尾"`。
  2. CLI 应仅在命中的内容范围后插入补充说明。
  3. 若命中不唯一，CLI 应返回明确错误，而不是模糊更新多处。

参考执行脚本（伪代码）：

```sh
chattool lark doc update doccnxxxxxxxxxxxx \
  --mode insert-after \
  --selection-with-ellipsis "开头...结尾" \
  --markdown "$(cat /tmp/insert.md)"
```
