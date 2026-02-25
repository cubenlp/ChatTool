# 交互卡片

飞书卡片（Interactive Card）是飞书机器人最强大的功能——不仅可以展示格式化信息，还支持按钮、表单等控件，用户点击后机器人可以动态更新卡片内容。

---

## 卡片结构

一张卡片由以下部分组成：

```python
card = {
    "config": {                    # 全局配置
        "wide_screen_mode": True,  # 宽屏模式
    },
    "header": {                    # 标题栏
        "title": {
            "tag": "plain_text",
            "content": "标题文字",
        },
        "template": "blue",        # 颜色主题
    },
    "elements": [                  # 内容块列表
        # ... 见下方元素说明
    ],
}
```

---

## 常用卡片元素

### Markdown 文本

```python
{
    "tag": "div",
    "text": {
        "tag": "lark_md",
        "content": "**加粗** _斜体_ ~~删除线~~ `code`\n\n支持换行",
    },
}
```

### 多列字段

```python
{
    "tag": "div",
    "fields": [
        {"is_short": True, "text": {"tag": "lark_md", "content": "**字段1**\n值1"}},
        {"is_short": True, "text": {"tag": "lark_md", "content": "**字段2**\n值2"}},
    ],
}
```

### 分割线

```python
{"tag": "hr"}
```

### 按钮（Action）

```python
{
    "tag": "action",
    "actions": [
        {
            "tag": "button",
            "text": {"tag": "plain_text", "content": "按钮文字"},
            "type": "primary",    # primary / default / danger
            "value": {            # 点击后传回的数据
                "action": "confirm",
                "task_id": "task_001",
            },
        },
    ],
}
```

### 备注

```python
{
    "tag": "note",
    "elements": [
        {"tag": "plain_text", "content": "这是备注信息，字体较小"}
    ],
}
```

### 图片

```python
{
    "tag": "img",
    "img_key": "img_xxxxxxxx",
    "alt": {"tag": "plain_text", "content": "图片描述"},
}
```

---

## 发送卡片

```python
import time

card = {
    "config": {"wide_screen_mode": True},
    "header": {
        "title": {"tag": "plain_text", "content": "📋 任务提醒"},
        "template": "blue",
    },
    "elements": [
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**任务**：完成飞书文档\n**截止**：今日 18:00\n**时间**：{time.strftime('%H:%M')}",
            },
        },
        {"tag": "hr"},
        {
            "tag": "action",
            "actions": [
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "✅ 已完成"},
                    "type": "primary",
                    "value": {"action": "done", "task_id": "t1"},
                },
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "⏰ 延期"},
                    "type": "default",
                    "value": {"action": "postpone", "task_id": "t1"},
                },
            ],
        },
    ],
}

resp = bot.send_card("rexwzh", "user_id", card)
if resp.success():
    print(f"卡片 id: {resp.data.message_id}")
```

---

## 处理按钮回调

用 `@bot.card_action("action_key")` 装饰器，根据 `value.action` 字段路由到对应处理函数：

```python
@bot.card_action("done")
def on_done(ctx):
    task_id = ctx.action_value.get("task_id")
    operator = ctx.operator_id
    
    # 更新卡片为「已完成」状态
    ctx.update_card({
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "✅ 任务已完成"},
            "template": "green",
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"操作人：{operator}\n完成时间：{time.strftime('%H:%M:%S')}",
                },
            }
        ],
    })
    
    # 弹出 Toast 提示（只有操作人能看到）
    ctx.toast("标记完成成功 ✅", type="success")

@bot.card_action("postpone")
def on_postpone(ctx):
    ctx.toast("已标记为延期", type="info")
```

### CardActionContext 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `ctx.action_value` | `dict` | 按钮的 `value` 字段内容 |
| `ctx.operator_id` | `str` | 点击按钮的用户 open_id |
| `ctx.message_id` | `str` | 卡片所在消息的 ID |

### ctx.update_card()

在回调响应中更新卡片内容（对所有人可见）：

```python
ctx.update_card(new_card_dict)
```

### ctx.toast()

弹出 Toast 提示（仅对点击操作的用户可见）：

```python
ctx.toast("操作成功", type="success")  # success / error / info / warning
```

---

## 主动更新已发送的卡片（Patch）

不依赖用户操作，主动更新卡片内容：

```python
import json, time
from lark_oapi.api.im.v1 import PatchMessageRequest, PatchMessageRequestBody

# 先发送卡片，记录 message_id
resp = bot.send_card("rexwzh", "user_id", initial_card)
msg_id = resp.data.message_id

# 模拟任务处理完成后更新卡片
time.sleep(3)

updated_card = {
    "config": {"wide_screen_mode": True},
    "header": {
        "title": {"tag": "plain_text", "content": "✅ 处理完成"},
        "template": "green",
    },
    "elements": [
        {"tag": "div", "text": {"tag": "lark_md",
         "content": f"完成时间：`{time.strftime('%H:%M:%S')}`"}}
    ],
}

patch_resp = bot.client.im.v1.message.patch(
    PatchMessageRequest.builder()
    .message_id(msg_id)
    .request_body(
        PatchMessageRequestBody.builder()
        .content(json.dumps(updated_card))
        .build()
    ).build()
)
print("更新状态:", "✅" if patch_resp.success() else f"❌ {patch_resp.msg}")
```

---

## 卡片颜色主题

| `template` | 颜色 | 典型场景 |
|------------|------|----------|
| `blue` | 蓝色 | 通知、待处理 |
| `green` | 绿色 | 成功、已完成 |
| `yellow` | 黄色 | 警告、注意 |
| `red` | 红色 | 错误、紧急告警 |
| `grey` | 灰色 | 进行中、已过期 |
| `purple` | 紫色 | 特殊标记 |

---

## 完整审批卡片示例

```python
import time

def make_approval_card(task_id, status="pending", operator=None):
    if status == "pending":
        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": "🔔 请假审批"},
                "template": "blue",
            },
            "elements": [
                {
                    "tag": "div",
                    "fields": [
                        {"is_short": True, "text": {"tag": "lark_md", "content": "**申请人**\nRex"}},
                        {"is_short": True, "text": {"tag": "lark_md", "content": "**假期类型**\n年假"}},
                        {"is_short": True, "text": {"tag": "lark_md", "content": "**天数**\n1天"}},
                        {"is_short": True, "text": {"tag": "lark_md",
                         "content": f"**申请时间**\n{time.strftime('%Y-%m-%d')}"}},
                    ],
                },
                {"tag": "hr"},
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "✅ 通过"},
                            "type": "primary",
                            "value": {"action": "approve", "task_id": task_id},
                        },
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "❌ 拒绝"},
                            "type": "danger",
                            "value": {"action": "reject", "task_id": task_id},
                        },
                    ],
                },
            ],
        }
    elif status == "approved":
        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": "✅ 已批准"},
                "template": "green",
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"审批人：{operator or '未知'}\n时间：{time.strftime('%H:%M:%S')}",
                    },
                }
            ],
        }
    else:  # rejected
        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": "❌ 已拒绝"},
                "template": "red",
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"审批人：{operator or '未知'}\n时间：{time.strftime('%H:%M:%S')}",
                    },
                }
            ],
        }


@bot.card_action("approve")
def on_approve(ctx):
    ctx.update_card(make_approval_card(
        ctx.action_value["task_id"], "approved", ctx.operator_id
    ))
    ctx.toast("审批已通过", type="success")


@bot.card_action("reject")
def on_reject(ctx):
    ctx.update_card(make_approval_card(
        ctx.action_value["task_id"], "rejected", ctx.operator_id
    ))
    ctx.toast("已拒绝", type="error")


# 发送审批卡片
bot.send_card("rexwzh", "user_id", make_approval_card("task_2024"))
bot.start()
```

---

## 卡片在线调试工具

飞书提供了可视化的卡片搭建工具，可以实时预览卡片效果：

🔗 [飞书卡片搭建工具](https://open.feishu.cn/tool/cardbuilder)

---

## 权限速查

| 操作 | 所需权限 |
|------|----------|
| 发送卡片 | `im:message` |
| 卡片引用回复 | `im:message` |
| 处理卡片回调 | 无额外权限，但需要在事件订阅中注册 `card.action.trigger` |
| 主动更新卡片（Patch） | `im:message` |
