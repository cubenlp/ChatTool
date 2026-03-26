# test_chattool_lark_send_card_task

任务导向地测试 `chattool lark send --card` 的卡片发送链路，目标是验证“把一张真实卡片发给默认用户并确认可见”。

## 元信息

- 命令：`chattool lark send [receiver] --card <path>`
- 目的：定义飞书卡片消息的基础发送任务，为后续交互卡、权限恢复卡等能力提供基线。
- 标签：`cli`
- 前置条件：具备飞书凭证、消息发送权限与默认接收者。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_DEFAULT_RECEIVER_ID`
  - `FEISHU_TEST_USER_ID`（可选；如未配置，默认复用 `FEISHU_DEFAULT_RECEIVER_ID`）
  - `FEISHU_TEST_USER_ID_TYPE`（可选；默认 `user_id`）
- 回滚：删除本地临时卡片 JSON；若需要，手动清理测试会话中的卡片消息。

## 用例 1：发送静态卡片到默认用户

- 初始环境准备：
  - 准备一份最小可用的卡片 JSON。
- 相关文件：
  - `<tmp>/card.json`

预期过程和结果：
  1. 执行 `chattool lark send --card <path>`。
  2. CLI 应自动使用默认接收者。
  3. 终端应输出发送成功与 `message_id`。
  4. 默认用户应收到渲染正常的卡片。

参考执行脚本（伪代码）：

```sh
chattool lark send --card /tmp/chattool-card.json
```

## 用例 2：发送带跳转按钮的卡片

- 初始环境准备：
  - 准备一份包含 URL 按钮的卡片 JSON。
- 相关文件：
  - `<tmp>/card-with-url.json`

预期过程和结果：
  1. 执行 `chattool lark send --card <path>`。
  2. 默认用户应收到可见的按钮。
  3. 点击按钮后，应跳转到目标页面，而不是报结构错误。

参考执行脚本（伪代码）：

```sh
chattool lark send --card /tmp/chattool-card-with-url.json
```
