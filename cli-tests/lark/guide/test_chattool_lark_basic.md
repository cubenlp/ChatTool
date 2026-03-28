# test_chattool_lark_basic

测试 `chattool lark` 的基础链路，聚焦当前保留的最小命令面：`info` / `send` / `chat`。

## 元信息

- 命令：`chattool lark <command> [args]`
- 目的：验证当前保留的飞书最小 CLI 仍可用。
- 标签：`cli`
- 前置条件：具备飞书凭证与至少一个可用接收者。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_DEFAULT_RECEIVER_ID`
  - `FEISHU_TEST_USER_ID`（可选；仅在 CLI 真实测试需要隔离目标时指定）
  - `FEISHU_TEST_USER_ID_TYPE`（可选；默认 `user_id`）
- 回滚：删除或忽略测试消息。

## 用例 1：获取机器人信息

- 初始环境准备：
  - 飞书凭证可用。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark info`，预期输出机器人名称与激活状态。

参考执行脚本（伪代码）：

```sh
chattool lark info
```

## 用例 2：发送文本消息

- 初始环境准备：
  - 准备接收者 user_id。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark send <user_id> "hello"`，预期返回 message_id。

参考执行脚本（伪代码）：

```sh
chattool lark send <user_id> "hello"
```

## 用例 3：本地对话

- 初始环境准备：
  - 无。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark chat`，预期进入本地对话模式。

参考执行脚本（伪代码）：

```sh
chattool lark chat
```

## 清理 / 回滚

- 删除或忽略测试消息。
