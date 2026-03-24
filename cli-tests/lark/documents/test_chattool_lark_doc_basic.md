# test_chattool_lark_doc_basic

测试 `chattool lark doc` 的基础链路，覆盖创建文档、获取文档、获取纯文本、查看块列表和追加文本。

## 元信息

- 命令：`chattool lark doc <command> [args]`
- 目的：验证飞书云文档 CLI 的基础命令可用。
- 标签：`cli`
- 前置条件：具备飞书凭证与文档权限。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_DEFAULT_RECEIVER_ID`
  - `FEISHU_TEST_USER_ID`（可选；仅在 CLI 真实测试需要隔离目标时指定）
  - `FEISHU_TEST_USER_ID_TYPE`（可选；默认 `user_id`）
- 回滚：删除测试文档或测试块（如适用）。

## 用例 1：创建文档

- 初始环境准备：
  - 飞书凭证可用，应用具备文档创建权限。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark doc create "测试文档"`。
  2. 预期返回 `document_id` 与标题。

参考执行脚本（伪代码）：

```sh
chattool lark doc create "测试文档"
```

## 用例 2：获取文档元信息

- 初始环境准备：
  - 准备一个可访问的 `document_id`。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark doc get <document_id>`。
  2. 预期返回标题和 revision。

参考执行脚本（伪代码）：

```sh
chattool lark doc get doccnxxxxxxxxxxxx
```

## 用例 3：获取纯文本内容

- 初始环境准备：
  - 准备一个有文本内容的 `document_id`。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark doc raw <document_id>`。
  2. 预期返回文档纯文本内容。

参考执行脚本（伪代码）：

```sh
chattool lark doc raw doccnxxxxxxxxxxxx
```

## 用例 4：查看块列表

- 初始环境准备：
  - 准备一个可访问的 `document_id`。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark doc blocks <document_id>`。
  2. 预期返回 block 列表与分页信息。

参考执行脚本（伪代码）：

```sh
chattool lark doc blocks doccnxxxxxxxxxxxx
```

## 用例 5：追加纯文本

- 初始环境准备：
  - 准备一个可写的 `document_id`。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark doc append-text <document_id> "hello"`。
  2. 预期返回追加成功与 revision 信息。

参考执行脚本（伪代码）：

```sh
chattool lark doc append-text doccnxxxxxxxxxxxx "hello"
```
