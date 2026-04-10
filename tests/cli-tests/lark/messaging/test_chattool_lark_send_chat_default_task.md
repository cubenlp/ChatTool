# test_chattool_lark_send_chat_default_task

任务导向地测试 `chattool lark send -t chat_id` 的默认群聊发送链路，目标是验证“把一条真实消息发给默认群聊”这条最小工作流。

## 元信息

- 命令：`chattool lark send -t chat_id [chat_id] <text>`
- 目的：定义默认群聊发送任务的真实 CLI 路径，避免群调试时每次都手工传 `chat_id`。
- 标签：`cli`
- 前置条件：具备飞书凭证、消息发送权限与一个可用群聊。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_DEFAULT_CHAT_ID`
- 回滚：删除或忽略测试消息；若群消息会干扰日常讨论，手动清理对应会话。

## 用例 1：使用默认群聊发送文本

- 初始环境准备：
  - 飞书凭证可用。
  - 已配置 `FEISHU_DEFAULT_CHAT_ID`。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark send -t chat_id "一条唯一的测试文本"`。
  2. CLI 应自动使用 `FEISHU_DEFAULT_CHAT_ID` 作为接收群聊。
  3. 终端应输出成功状态与 `message_id`。
  4. 默认群聊应实际收到这条测试消息。

参考执行脚本（伪代码）：

```sh
chattool lark send -t chat_id "cli task: send group text $(date +%s)"
```
