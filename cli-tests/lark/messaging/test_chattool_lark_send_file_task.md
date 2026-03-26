# test_chattool_lark_send_file_task

任务导向地测试 `chattool lark send --file/--image` 的资源发送链路，目标是验证“把本地文件交给默认用户”这条真实工作流。

## 元信息

- 命令：`chattool lark send [receiver] --file <path>`、`chattool lark send [receiver] --image <path>`
- 目的：定义消息附件投递任务，覆盖本地文件与图片的真实发送路径。
- 标签：`cli`
- 前置条件：具备飞书凭证、资源发送权限与默认接收者。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_DEFAULT_RECEIVER_ID`
  - `FEISHU_TEST_USER_ID`（可选；如未配置，默认复用 `FEISHU_DEFAULT_RECEIVER_ID`）
  - `FEISHU_TEST_USER_ID_TYPE`（可选；默认 `user_id`）
- 回滚：删除本地临时文件；若需要，手动清理测试会话中的附件消息。

## 用例 1：发送本地文本文件

- 初始环境准备：
  - 准备一个本地文本文件。
- 相关文件：
  - `<tmp>/upload.txt`

预期过程和结果：
  1. 执行 `chattool lark send --file <path>`。
  2. CLI 应自动使用默认接收者。
  3. 终端应输出发送成功与 `message_id`。
  4. 默认用户应收到带附件的消息。

参考执行脚本（伪代码）：

```sh
chattool lark send --file /tmp/chattool-send-file.txt
```

## 用例 2：发送本地图片

- 初始环境准备：
  - 准备一张小尺寸图片。
- 相关文件：
  - `<tmp>/image.png`

预期过程和结果：
  1. 执行 `chattool lark send --image <path>`。
  2. 终端应输出发送成功与 `message_id`。
  3. 默认用户应实际收到图片消息。

参考执行脚本（伪代码）：

```sh
chattool lark send --image /tmp/chattool-send-image.png
```
