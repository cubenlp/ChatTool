# test_chattool_lark_reply_task

任务导向地测试 `chattool lark reply` 的引用回复链路，目标是验证“对一条刚发出的真实消息做回复”。

## 元信息

- 命令：`chattool lark reply <message_id> <text>`
- 目的：定义消息确认与跟进的最小回复任务。
- 标签：`cli`
- 前置条件：具备飞书凭证、消息发送权限与默认接收者。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_DEFAULT_RECEIVER_ID`
  - `FEISHU_TEST_USER_ID`（可选；如未配置，默认复用 `FEISHU_DEFAULT_RECEIVER_ID`）
  - `FEISHU_TEST_USER_ID_TYPE`（可选；默认 `user_id`）
- 回滚：如需要，手动清理原始消息和回复消息。

## 用例 1：对刚发出的消息做引用回复

- 初始环境准备：
  - 先成功发送一条唯一文本消息，并拿到 `message_id`。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark reply <message_id> "收到"`。
  2. 终端应输出回复成功与新的 `message_id`。
  3. 默认用户应在同一会话中看到引用回复效果。

参考执行脚本（伪代码）：

```sh
MESSAGE_ID=$(chattool lark send "cli task: reply seed" | sed -n 's/.*message_id=//p')
chattool lark reply "$MESSAGE_ID" "收到"
```
