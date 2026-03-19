# 飞书消息与文档 Skill

## 目标

通过 `chattool lark` 快速发送飞书消息/文件，并完成基础的机器人验证与权限检查。

## 前置条件

1) 配置飞书机器人凭证：

```bash
chattool env init -t feishu
# 按提示填写 FEISHU_APP_ID / FEISHU_APP_SECRET
```

2) 验证机器人：

```bash
chattool lark info
```

3) 检查权限（可选）：

```bash
chattool lark scopes
```

必要权限：
- `im:message:send_as_bot`
- 发送文件需 `im:file`

## 常用操作（CLI）

### 发送文本消息

```bash
chattool lark send <receiver_id> "你好，世界"
```

默认 `receiver_id` 类型为 `user_id`。如需其他类型，请加 `-t`：

```bash
# 发送到群聊
chattool lark send <chat_id> "群消息" -t chat_id

# 使用 open_id
chattool lark send <open_id> "你好" -t open_id
```

### 发送图片

```bash
chattool lark send <receiver_id> --image ./photo.jpg
```

### 发送文件

```bash
chattool lark send <receiver_id> --file ./report.pdf
```

### 发送卡片/富文本

```bash
chattool lark send <receiver_id> --card ./card.json
chattool lark send <receiver_id> --post ./post.json
```

## 常见问题

- **提示权限不足**：在飞书开放平台补全权限，并重新发布应用。
- **发送失败或收不到消息**：确认机器人已加入群聊，且用户在可见范围内。

## 备注

如需更复杂的消息编排（自动拉群、分享文档权限等），建议使用飞书 OpenAPI，并在脚本中调用（无需在此 Skill 内展开）。
