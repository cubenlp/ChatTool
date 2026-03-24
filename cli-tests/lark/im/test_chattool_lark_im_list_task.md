# test_chattool_lark_im_list_task

任务导向地测试 `chattool lark im list` 的历史消息读取链路，目标是验证“从一个真实会话中取回近期消息并继续做人工核对”。

## 元信息

- 命令：`chattool lark im list --chat-id <chat_id>`
- 目的：定义 IM 历史消息读取任务，作为 thread/search 扩展前的读取基线。
- 标签：`cli`
- 前置条件：具备飞书凭证、消息读取权限与可访问会话。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_DEFAULT_RECEIVER_ID`
  - `FEISHU_TEST_USER_ID`（可选；如未配置，默认复用 `FEISHU_DEFAULT_RECEIVER_ID`）
  - `FEISHU_TEST_USER_ID_TYPE`（可选；默认 `user_id`）
- 回滚：通常为只读；如为准备测试临时发送了种子消息，可视需要手动清理。

## 用例 1：读取目标会话最近消息

- 初始环境准备：
  - 准备一个真实可访问的 `chat_id`。
  - 若近期无消息，可先向该会话发一条唯一测试文本。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark im list --chat-id <chat_id> --relative-hours 24`。
  2. CLI 应返回消息列表，而不是空的结构错误或权限错误。
  3. 若前面准备了唯一测试文本，结果中应能人工定位到该消息。

参考执行脚本（伪代码）：

```sh
chattool lark im list --chat-id oc_xxx --relative-hours 24
```
