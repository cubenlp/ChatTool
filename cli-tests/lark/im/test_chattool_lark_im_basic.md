# test_chattool_lark_im_basic

测试目标 `chattool lark im ...` 命令面的基础链路，先固定接口与真实测试场景，再实现 CLI。

## 元信息

- 命令：`chattool lark im <command> [args]`
- 目的：定义飞书 IM 读取 CLI 的第一阶段命令边界与真实测试路径。
- 标签：`cli`
- 前置条件：具备飞书凭证、消息读取权限与可访问会话。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_TEST_USER_ID`
  - `FEISHU_TEST_USER_ID_TYPE`
- 回滚：删除测试消息与临时下载文件。

## 当前阶段已落地命令

- `chattool lark im list --chat-id <chat_id>`
- `chattool lark im download <message_id> <file_key> --type <image|file|audio|video>`

## 后续规划命令

- `chattool lark im thread <thread_id>`
- `chattool lark im search --query <text>`

## 用例 1：读取单聊或群聊消息

- 初始环境准备：
  - 准备 `chat_id`。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark im list --chat-id <chat_id>`。
  2. 预期返回消息列表。

参考执行脚本（伪代码）：

```sh
chattool lark im list --chat-id oc_xxx
```

## 用例 2：下载消息资源

- 初始环境准备：
  - 准备 `message_id`、`file_key` 和资源类型。
- 相关文件：
  - `<tmp>/downloads/`

预期过程和结果：
  1. 执行 `chattool lark im download <message_id> <file_key> --type image`。
  2. 预期下载成功并返回本地文件路径。

参考执行脚本（伪代码）：

```sh
chattool lark im download om_xxx img_v3_xxx --type image
```
