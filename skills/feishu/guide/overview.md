---
name: feishu
description: Use `chattool lark` as the default entry for Feishu/Lark bot verification, scope checks, send/upload/reply flows, and local debugging. Prefer CLI arguments for business inputs and avoid extra env vars that may conflict with external gateways.
version: 0.1.0
---

## 对应 CLI 用法

- 当前总入口仍然是 `chattool lark`
- 常用起点：
  - `chattool lark info`
  - `chattool lark scopes`
  - `chattool lark send`
  - `chattool lark upload`
  - `chattool lark reply`
  - `chattool lark listen`
  - `chattool lark chat`
  - `chattool lark doc ...`
- 下方保留 archive 中旧主 skill 的原始说明，方便和当前 CLI 入口对照

# 飞书 CLI Skill

## 目标

优先使用 `chattool lark` 完成飞书机器人的验证、权限检查、消息发送、资源上传、引用回复和调试。

不要先写飞书 OpenAPI 脚本，也不要默认退回 SDK 示例。只有当 `chattool lark` 明确不覆盖目标能力时，才考虑补脚本或扩 CLI。

## 凭证来源

`chattool lark` 当前默认从 ChatTool 环境变量或配置文件读取凭证：

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`

推荐先执行：

```bash
chattool env init -t feishu
```

也可以手工导出：

```bash
export FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
export FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

如果你经常把测试消息发给固定用户，可以再配一个可选项：

```bash
chattool env set FEISHU_DEFAULT_RECEIVER_ID=f25gc16d
```

## 输入约定

- 凭证放环境变量或 ChatTool 配置。
- 业务输入优先走 CLI 参数，例如 `receiver`、`text`、`message_id`、`--type`、`--image`、`--file`。
- 如果当前进程同时被 OpenClaw、消息网关或其他入口复用，不要再新增临时环境变量传业务参数，避免语义冲突。

## 当前推荐命令

### 1. 验证机器人是否可用

```bash
chattool lark info
```

用于确认 `FEISHU_APP_ID` / `FEISHU_APP_SECRET` 是否正确，以及机器人是否已激活。

### 2. 检查权限

```bash
chattool lark scopes
chattool lark scopes -f im
chattool lark scopes -g
chattool lark scopes -a -g
```

发送消息前，至少确认消息相关权限已经申请并授权。

### 3. 发送文本

```bash
chattool lark send "你好，世界"
chattool lark send <receiver_id> "你好，世界"
chattool lark send <chat_id> "群通知" -t chat_id
chattool lark send <open_id> "你好" -t open_id
```

默认接收者类型是 `user_id`。

### 4. 发送图片、文件、卡片、富文本

```bash
chattool lark send <receiver_id> --image ./photo.jpg
chattool lark send <receiver_id> --file ./report.pdf
chattool lark send <receiver_id> --card ./card.json
chattool lark send <receiver_id> --post ./post.json
```

### 5. 单独上传资源

```bash
chattool lark upload ./photo.jpg
chattool lark upload ./report.pdf
chattool lark upload ./data.bin -t file
```

适合先拿到 `image_key` / `file_key`，再嵌入卡片或富文本结构。

### 6. 引用回复消息

```bash
chattool lark reply <message_id> "收到，已处理"
```

### 7. 调试消息接收

```bash
chattool lark listen
chattool lark listen -v
chattool lark listen -l DEBUG
```

用于验证长连接模式、事件订阅和消息接收链路。

### 8. 本地调试 AI 对话

```bash
chattool lark chat
chattool lark chat --system "你是一名飞书助手"
chattool lark chat --user test_user
```

这不会向飞书发消息，只是在终端里复用同一套会话能力做本地验证。

### 9. 云文档

```bash
chattool lark doc create "周报草稿"
chattool lark doc get <document_id>
chattool lark doc raw <document_id>
chattool lark doc blocks <document_id>
chattool lark doc append-text <document_id> "今天完成了接口整理"
chattool lark notify-doc "周报草稿" "今天完成了接口整理"
chattool lark notify-doc "周报草稿" --append-file ./daily.md --open
```

适合把机器人输出直接沉淀到飞书文档里，而不是只回消息。

## 处理原则

当用户提出“发一条飞书消息”“给群里传文件”“检查权限”“验证机器人是否可用”“看下监听链路”这类请求时：

1. 优先使用 `chattool lark`。
2. 直接把业务输入映射到 CLI 参数。
3. 不要为一次性消息内容或接收者引入新的环境变量。
4. CLI 已覆盖的能力，不要退回到手写 OpenAPI 请求。

## 常见问题

- 权限不足：先执行 `chattool lark scopes -f im`，再去飞书开放平台补权限并发布应用。
- 消息发送失败：确认机器人已加入目标群聊，或目标用户在应用可见范围内。
- 监听不到消息：确认飞书后台已开启长连接模式，并订阅 `im.message.receive_v1`。
