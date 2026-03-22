# 飞书 Skill：消息与调试

## 发送文本

```bash
chattool lark send "你好，世界"
chattool lark send <receiver_id> "你好，世界"
chattool lark send <chat_id> "群通知" -t chat_id
chattool lark send <open_id> "你好" -t open_id
```

默认接收者类型是 `user_id`。

## 发送图片、文件、卡片、富文本

```bash
chattool lark send <receiver_id> --image ./photo.jpg
chattool lark send <receiver_id> --file ./report.pdf
chattool lark send <receiver_id> --card ./card.json
chattool lark send <receiver_id> --post ./post.json
```

## 上传资源

```bash
chattool lark upload ./photo.jpg
chattool lark upload ./report.pdf
chattool lark upload ./data.bin -t file
```

适合先拿到 `image_key` / `file_key` 再组合其他消息结构。

## 引用回复

```bash
chattool lark reply <message_id> "收到，已处理"
```

## 调试监听

```bash
chattool lark listen
chattool lark listen -v
chattool lark listen -l DEBUG
```

使用前确认：

- 飞书后台已启用长连接模式。
- 已订阅 `im.message.receive_v1`。
- 权限已经发布并生效。

## 本地终端调试 AI 对话

```bash
chattool lark chat
chattool lark chat --system "你是一名飞书助手"
chattool lark chat --user debug_user
```

这个命令不会向飞书发消息，只是在终端里复用同一套会话能力。
