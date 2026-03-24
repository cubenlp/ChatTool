# test_chattool_lark_troubleshoot_message_task

任务导向地测试消息相关排障链路，目标是验证“发送失败后，能够沿着诊断命令定位是权限、接收者范围还是事件配置问题”。

## 元信息

- 命令：`chattool lark troubleshoot doctor`、`chattool lark troubleshoot check-scopes`、`chattool lark troubleshoot check-events`、`chattool lark troubleshoot check-card-action`
- 目的：定义消息排障任务，而不只是验证单个诊断子命令存在。
- 标签：`cli`
- 前置条件：具备飞书凭证，并至少准备一个正常配置或一个带已知问题的配置。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_DEFAULT_RECEIVER_ID`
  - `FEISHU_TEST_USER_ID`（可选；如未配置，默认复用 `FEISHU_DEFAULT_RECEIVER_ID`）
  - `FEISHU_TEST_USER_ID_TYPE`（可选；默认 `user_id`）
- 回滚：通常为只读；若执行了 `--send-card`，可视需要手动清理测试卡片消息。

## 用例 1：对消息发送问题执行整套排障

- 初始环境准备：
  - 准备一条已知失败或疑似失败的消息发送场景。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark troubleshoot doctor`。
  2. 执行 `chattool lark troubleshoot check-scopes`。
  3. 如问题与监听或交互卡有关，再执行 `check-events` 与 `check-card-action`。
  4. 终端应能把问题逐步收敛到权限、接收者范围、事件订阅或卡片交互配置中的一类。

参考执行脚本（伪代码）：

```sh
chattool lark troubleshoot doctor
chattool lark troubleshoot check-scopes
chattool lark troubleshoot check-events
chattool lark troubleshoot check-card-action
```
