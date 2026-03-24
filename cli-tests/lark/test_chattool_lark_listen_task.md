# test_chattool_lark_listen_task

任务导向地测试 `chattool lark listen` 的消息监听链路，目标是验证“CLI 能通过长连接看到真实会话里的新消息事件”。

## 元信息

- 命令：`chattool lark listen [-v] [-l <level>]`
- 目的：定义飞书消息接收链路的真实监听任务。
- 标签：`cli`
- 前置条件：具备飞书凭证，飞书后台已启用长连接并订阅消息事件。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_DEFAULT_RECEIVER_ID`
  - `FEISHU_TEST_USER_ID`（可选；如未配置，默认复用 `FEISHU_DEFAULT_RECEIVER_ID`）
  - `FEISHU_TEST_USER_ID_TYPE`（可选；默认 `user_id`）
  - 飞书后台开启长连接与消息接收事件
- 回滚：通常为只读；若监听期间主动发送了测试消息，可视需要手动清理会话。

## 用例 1：监听默认用户会话中的新消息

- 初始环境准备：
  - 在一个终端启动监听。
  - 在另一个终端或飞书客户端准备向机器人发送一条测试消息。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark listen -v`。
  2. 终端应输出连接成功日志。
  3. 当默认用户向机器人发送新消息后，终端应打印出消息事件、发送者和消息内容。

参考执行脚本（伪代码）：

```sh
chattool lark listen -v
```
