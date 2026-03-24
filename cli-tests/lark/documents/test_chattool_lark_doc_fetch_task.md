# test_chattool_lark_doc_fetch_task

任务导向地测试文档读取链路，目标是验证“对一篇真实文档做查看、取纯文本和看 block 结构”。

## 元信息

- 命令：`chattool lark doc get <document_id>`、`chattool lark doc raw <document_id>`、`chattool lark doc blocks <document_id>`
- 目的：定义文档读取任务，作为后续更新和结构化写入的读取基线。
- 标签：`cli`
- 前置条件：具备飞书凭证、docx 读取权限与一篇可访问文档。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_DEFAULT_RECEIVER_ID`
  - `FEISHU_TEST_USER_ID`（可选；仅在需要隔离测试用户时额外指定）
  - `FEISHU_TEST_USER_ID_TYPE`（可选；默认 `user_id`）
- 回滚：通常为只读；若为准备测试临时创建了文档，可在结束后删除。

## 用例 1：查看文档元信息

- 初始环境准备：
  - 准备一个可访问的 `document_id`。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark doc get <document_id>`。
  2. 终端应输出标题、revision 等基本信息。

参考执行脚本（伪代码）：

```sh
chattool lark doc get doccnxxxxxxxxxxxx
```

## 用例 2：获取纯文本内容

- 初始环境准备：
  - 准备一篇已经包含唯一文本的文档。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark doc raw <document_id>`。
  2. 终端应输出文档纯文本内容。
  3. 若文档中预先写入了唯一文本，应能在输出中人工定位到它。

参考执行脚本（伪代码）：

```sh
chattool lark doc raw doccnxxxxxxxxxxxx
```

## 用例 3：查看 block 结构

- 初始环境准备：
  - 准备一篇包含多段内容的文档。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark doc blocks <document_id>`。
  2. 终端应输出 block 列表与分页信息。
  3. 输出应可作为后续定位更新与结构化调试的基础。

参考执行脚本（伪代码）：

```sh
chattool lark doc blocks doccnxxxxxxxxxxxx
```
