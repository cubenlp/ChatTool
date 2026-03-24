# test_chattool_lark_send_permission_recovery_task

任务导向地测试 `chattool lark send` 在权限不足时的恢复链路，目标是验证“发送失败后自动诊断并发出权限引导卡”。

## 元信息

- 命令：`chattool lark send ...`
- 目的：定义发送失败后的权限恢复任务，覆盖 scopes 诊断、引导卡导出与自动发卡。
- 标签：`cli`
- 前置条件：具备两套可切换飞书配置，其中一套故意缺少消息发送相关权限。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_DEFAULT_RECEIVER_ID`
  - `FEISHU_TEST_USER_ID`（可选；如未配置，默认复用 `FEISHU_DEFAULT_RECEIVER_ID`）
  - `FEISHU_TEST_USER_ID_TYPE`（可选；默认 `user_id`）
  - 一套受限 profile 或 `.env`，例如 `limited-send`
- 回滚：删除导出的权限引导卡 JSON；若自动发卡成功，视需要手动清理权限引导卡消息。

## 用例 1：权限不足时自动诊断并导出权限引导卡

- 初始环境准备：
  - 使用一套故意缺少 `im` 发送能力的飞书配置。
- 相关文件：
  - `/tmp/chattool-lark-permission-card.json`

预期过程和结果：
  1. 执行 `chattool lark send "一条会失败的测试消息" -e limited-send`。
  2. CLI 应输出发送失败与权限相关错误码。
  3. CLI 应继续执行 scopes 诊断，而不是只停在失败提示。
  4. CLI 应把权限引导卡 JSON 导出到 `/tmp/chattool-lark-permission-card.json`。

参考执行脚本（伪代码）：

```sh
chattool lark send "cli task: permission recovery" -e limited-send
```

## 用例 2：有默认用户时自动发送权限引导卡

- 初始环境准备：
  - 仍使用受限配置。
  - 已配置 `FEISHU_DEFAULT_RECEIVER_ID`，并允许该接收者接收卡片。
- 相关文件：
  - `/tmp/chattool-lark-permission-card.json`

预期过程和结果：
  1. 执行同一条失败发送命令。
  2. CLI 在导出卡片后，应继续尝试把权限引导卡发给默认用户或测试用户。
  3. 终端应输出权限引导卡的 `message_id` 或自动发卡失败原因。

参考执行脚本（伪代码）：

```sh
chattool lark send "cli task: permission recovery" -e limited-send
```
