# test_chattool_lark_send_text_task

任务导向地测试 `chattool lark send` 的文本发送链路，目标是验证“把一条真实消息发给默认用户”这条最小工作流。

## 元信息

- 命令：`chattool lark send [receiver] <text>`
- 目的：定义默认消息发送任务的真实 CLI 路径，作为后续卡片、文件、权限恢复等任务的公共基线。
- 标签：`cli`
- 前置条件：具备飞书凭证、消息发送权限与默认接收者。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_DEFAULT_RECEIVER_ID`
  - `FEISHU_DEFAULT_CHAT_ID`（可选；仅在默认群聊发送测试里使用）
- 回滚：删除或忽略测试消息；若消息会干扰日常对话，手动清理对应会话。

## 用例 1：使用默认用户发送文本

- 初始环境准备：
  - 飞书凭证可用。
  - 已配置 `FEISHU_DEFAULT_RECEIVER_ID`。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark send "一条唯一的测试文本"`。
  2. CLI 应自动使用 `FEISHU_DEFAULT_RECEIVER_ID` 作为接收者。
  3. 终端应输出成功状态与 `message_id`。
  4. 默认用户应实际收到这条测试消息。

参考执行脚本（伪代码）：

```sh
chattool lark send "cli task: send text $(date +%s)"
```

## 用例 2：显式接收者优先于默认用户

- 初始环境准备：
  - 准备一个可接收消息的 `user_id` 或 `chat_id`。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark send <receiver_id> "一条唯一的测试文本"`。
  2. CLI 应优先使用显式传入的接收者，而不是 `FEISHU_DEFAULT_RECEIVER_ID`。
  3. 终端应输出成功状态与 `message_id`。

参考执行脚本（伪代码）：

```sh
chattool lark send f25gc16d "cli task: explicit receiver $(date +%s)"
```
