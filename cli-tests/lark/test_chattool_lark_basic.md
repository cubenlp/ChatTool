# test_chattool_lark_basic

测试 `chattool lark` 的基础链路，覆盖 info / scopes / send / upload / reply / listen / chat，并把它作为后续 `chattool lark <topic> ...` 扩展的公共基线。

## 元信息

- 命令：`chattool lark <command> [args]`
- 目的：验证飞书 CLI 的核心命令可用。
- 标签：`cli`
- 前置条件：具备飞书凭证与测试用户。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_DEFAULT_RECEIVER_ID`
  - `FEISHU_TEST_USER_ID`
  - `FEISHU_TEST_USER_ID_TYPE`
- 回滚：删除测试消息与上传文件（如适用）。

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

## 用例 2：查看权限 scopes

- 初始环境准备：
  - 飞书凭证可用。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark scopes`，预期输出已授权权限列表。

参考执行脚本（伪代码）：

```sh
chattool lark scopes
```

## 用例 3：发送文本消息

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

补充说明：

- 如果 `send` 因权限问题失败，CLI 应优先做一次 scopes 诊断。
- 若已配置 `FEISHU_TEST_USER_ID` 或 `FEISHU_DEFAULT_RECEIVER_ID`，CLI 应尽量自动发送权限引导卡。
- 若自动发卡也失败，CLI 至少应导出一份权限引导卡 JSON，供继续排障。

## 用例 4：上传文件

- 初始环境准备：
  - 准备本地文件。
- 相关文件：
  - `<tmp>/upload.bin`

预期过程和结果：
  1. 执行 `chattool lark upload <path>`，预期返回 image_key 或 file_key。

参考执行脚本（伪代码）：

```sh
chattool lark upload /tmp/upload.bin
```

## 用例 5：引用回复

- 初始环境准备：
  - 准备可回复的 message_id。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark reply <message_id> "收到"`，预期返回回复成功。

参考执行脚本（伪代码）：

```sh
chattool lark reply om_xxx "收到"
```

## 用例 6：监听与本地对话

- 初始环境准备：
  - 飞书事件订阅已配置（listen）。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark listen --verbose`，预期输出事件日志。
  2. 执行 `chattool lark chat`，预期进入本地对话模式。

参考执行脚本（伪代码）：

```sh
chattool lark listen --verbose
chattool lark chat
```

## 清理 / 回滚

- 删除测试消息与本地临时文件。
