# 消息发送

本章介绍 `LarkBot` 支持的所有消息发送方式，包括文本、富文本、图片、文件和卡片。

---

## 接收者 ID 类型

所有发送方法都需要指定 `receive_id`（接收者 ID）和 `receive_id_type`（ID 类型）：

| `receive_id_type` | 说明 | 典型值 |
|-------------------|------|--------|
| `open_id` | 用户在应用内的唯一 ID | `ou_xxxxxxxx` |
| `user_id` | 用户在企业内的工号 | `rexwzh` |
| `union_id` | 用户跨应用唯一 ID | `on_xxxxxxxx` |
| `email` | 用户邮箱 | `user@company.com` |
| `chat_id` | 群聊 ID（向群发送） | `oc_xxxxxxxx` |

!!! tip
    使用 `user_id` 方式发送时，需要申请 `contact:user.employee_id:readonly` 权限。  
    使用 `open_id` 最为常见，无额外权限要求。

---

## 文本消息

```python
resp = bot.send_text("rexwzh", "user_id", "你好！👋")
```

### @ 用户

文本消息中可以使用 `<at>` 标签 @ 用户：

```python
# @ 指定用户
bot.send_text("oc_group", "chat_id",
    '<at user_id="rexwzh">Rex</at> 有个任务需要处理')

# @ 所有人（仅群聊有效）
bot.send_text("oc_group", "chat_id",
    '<at user_id="all">所有人</at> 下午3点开会，请准时')
```

---

## 富文本消息 (Post)

富文本支持多语言版本、标题、段落、超链接、@ 用户、代码块等。

```python
content = {
    "zh_cn": {
        "title": "📋 项目进度更新",
        "content": [
            # 一个列表 = 一行
            [
                {"tag": "text", "text": "本周进度："},
                {"tag": "a", "text": "查看详情", "href": "https://example.com"},
            ],
            [
                {"tag": "text", "text": "负责人："},
                {"tag": "at", "user_id": "rexwzh"},
            ],
            [
                {"tag": "code_block", "language": "python", "text": "print('hello')"},
            ],
        ],
    }
}

resp = bot.send_post("oc_group", "chat_id", content)
```

### 富文本 Tag 速查

| `tag` | 说明 | 必填字段 |
|-------|------|----------|
| `text` | 普通文字 | `text` |
| `a` | 超链接 | `text`, `href` |
| `at` | @ 用户 | `user_id` |
| `img` | 内嵌图片 | `image_key` |
| `code_block` | 代码块 | `language`, `text` |
| `hr` | 水平分割线 | — |

---

## 图片消息

=== "一步发送（推荐）"

    ```python
    resp = bot.send_image_file("rexwzh", "user_id", "photo.jpg")
    ```

=== "CLI"

    ```bash
    chattool lark send rexwzh --image photo.jpg
    ```

=== "分步操作"

    ```python
    # 1. 上传图片，获取 image_key
    upload_resp = bot.upload_image("photo.jpg")
    image_key = upload_resp.data.image_key

    # 2. 用 image_key 发送
    resp = bot.send_image("rexwzh", "user_id", image_key)
    ```

!!! tip "仅上传不发送"
    如果只需要获取 `image_key`（例如用于富文本或卡片内嵌图片），可以单独调用：

    ```python
    resp = bot.upload_image("photo.jpg")
    print(resp.data.image_key)  # img_v3_xxxx
    ```

    CLI: `chattool lark upload photo.jpg`

---

## 文件消息

=== "一步发送"

    ```python
    resp = bot.send_file("rexwzh", "user_id", "report.pdf")
    ```

=== "CLI"

    ```bash
    chattool lark send rexwzh --file report.pdf
    ```

=== "分步操作"

    ```python
    upload_resp = bot.upload_file("report.pdf")
    file_key = upload_resp.data.file_key
    # 可以用 file_key 发送给多个人
    ```

---

## 交互卡片 (Interactive)

卡片支持按钮、下拉框等控件，用户点击后触发回调。详见 [交互卡片](cards.md)。

```python
card = {
    "config": {"wide_screen_mode": True},
    "header": {
        "title": {"tag": "plain_text", "content": "🔔 通知"},
        "template": "blue",
    },
    "elements": [
        {
            "tag": "div",
            "text": {"tag": "lark_md", "content": "**任务**：完成周报\n**截止**：今日 18:00"},
        },
        {"tag": "hr"},
        {
            "tag": "action",
            "actions": [
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "✅ 已完成"},
                    "type": "primary",
                    "value": {"action": "done"},
                }
            ],
        },
    ],
}

resp = bot.send_card("rexwzh", "user_id", card)
```

### 卡片颜色主题

| `template` | 效果 | 场景 |
|------------|------|------|
| `blue` | 蓝色 | 通知、提醒 |
| `green` | 绿色 | 成功、完成 |
| `yellow` | 黄色 | 警告、待处理 |
| `red` | 红色 | 错误、紧急 |
| `grey` | 灰色 | 已过期、进行中 |
| `purple` | 紫色 | 特殊标记 |

---

## 引用回复

引用某条消息（在该消息下方嵌套显示）：

```python
# 引用回复文本
bot.reply("om_message_id", "收到，正在处理 ✅")

# 引用回复卡片
bot.reply_card("om_message_id", card_dict)
```

!!! note
    `reply()` 和 `reply_card()` 需要知道原始消息的 `message_id`。  
    在 `@bot.on_message` 处理器中，可以通过 `ctx.message_id` 获取，也可以直接用 `ctx.reply()` 快捷方法。

---

## 使用 BaseMessage 对象

`elements.py` 中定义了强类型的消息对象，可以作为 `send_message()` 的参数：

```python
from chattool.tools.lark.elements import TextMessage, PostMessage, InteractiveMessage

# 文本消息对象
msg = TextMessage("你好")
bot.send_message("rexwzh", "user_id", msg)

# 富文本消息对象
post = PostMessage(
    title="周报",
    content=[[{"tag": "text", "text": "本周完成了需求文档"}]]
)
bot.send_message("oc_group", "chat_id", post)
```

---

## 错误处理

```python
resp = bot.send_text("rexwzh", "user_id", "你好")

if not resp.success():
    code = resp.code
    if code == 99991672:
        print("权限不足，请申请 contact:user.employee_id:readonly")
    elif code == 99991663:
        print("用户不在应用可见范围内")
    else:
        print(f"发送失败: {code} {resp.msg}")
else:
    print(f"发送成功: {resp.data.message_id}")
```

---

## 权限速查

| 操作 | 所需权限 |
|------|----------|
| 发送消息（chat_id / open_id） | `im:message` |
| 发送消息（user_id 方式） | `im:message` + `contact:user.employee_id:readonly` |
| 上传图片/文件 | `im:resource` |
| 引用回复 | `im:message` |
