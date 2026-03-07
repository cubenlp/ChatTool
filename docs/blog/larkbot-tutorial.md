# 如何用 Python 10分钟写一个飞书 AI 助手？(ChatTool 全攻略)

![LarkBot Tutorial Cover](larkbot-tutorial-cover.svg)

今天这篇教程，我们来手把手教你用 Python + `chattool` 开发一个功能强大的飞书（Lark）机器人。不仅能聊天，还能发卡片、处理按钮点击，甚至直接在命令行里跑起来。

不整虚的，直接上干货。

---

## 为什么要用 `chattool`？

飞书开放平台的 API 很强大，但文档浩如烟海，光是鉴权（Token 管理）、事件解密、消息结构体就能劝退不少人。

`chattool` 的目标就是**让代码像说话一样简单**。它帮你搞定了：
- 自动管理 Tenant Access Token（不用自己刷新）
- 封装了 WebSocket 长连接（本地开发无需内网穿透）
- 极简的消息发送接口（不用手拼 JSON）
- 内置 AI 会话管理（自动记忆上下文）

Ready? Let's go.

---

## 第一步：搞定飞书后台（这步最繁琐，但只需一次）

在写代码之前，我们需要先去 [飞书开放平台](https://open.feishu.cn/) 申请一个“身份证”。

> 如果你已经有 App ID 和 Secret，可以跳过此步。详细步骤请参考：[飞书平台配置教程](../larkbot/feishu-setup.md)

### 1. 创建应用
登录开发者后台，点击「**创建企业自建应用**」，起个好听的名字，比如 `AI 摸鱼助手`。

![创建企业自建应用](https://qiniu.wzhecnu.cn/FileBed/source/20260226020952.png)

### 2. 拿到钥匙 (App ID & Secret)
进入「凭证与基础信息」，把 **App ID** 和 **App Secret** 复制下来，待会要用。

![凭证与基础信息](https://qiniu.wzhecnu.cn/FileBed/source/20260226021130.png)

### 3. 开启机器人
在「应用功能」→「机器人」中，把开关打开。这一步不做，机器人就是个摆设。

![开启机器人能力](https://qiniu.wzhecnu.cn/FileBed/source/20260226024745.png)

### 4. 申请权限 (Scopes)
机器人能干什么，全靠权限。在「权限管理」中申请以下 3 个核心权限：
- `im:message`（我要发消息）
- `im:message.receive_v1`（我要收消息）
- `contact:user.employee_id:readonly`（我要知道谁在跟我说话）

![权限管理](https://qiniu.wzhecnu.cn/FileBed/source/20260226024831.png)

### 5. 订阅消息事件
怎么知道有人给机器人发消息了？
推荐用 **WebSocket 长连接**（官方叫“使用长连接接收事件”）。好处是：**不需要公网 IP，不需要配置域名，本地电脑直接能跑！**

记得添加订阅事件：`接收消息 v2.0` (`im.message.receive_v1`)。

![选择长连接接收事件](https://qiniu.wzhecnu.cn/FileBed/source/20260226030553.png)

### 6. 发布应用
最后，创建版本并点击「申请发布」。

![创建版本并提交发布](https://qiniu.wzhecnu.cn/FileBed/source/20260226031345.png)

---

## 第二步：Hello World，五行代码跑起来

环境配置好了，终于可以写代码了。

### 1. 安装库
```bash
pip install "chattool[tools]"
```

### 2. 配置环境变量
通过 `chatenv init -i -t lark` 初始化配置，填入刚才拿到的钥匙：

```bash
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. 写个复读机

新建 `bot.py`，代码如下：

```python
from chattool.tools.lark import LarkBot

# 自动读取环境变量中的 ID 和 Secret
bot = LarkBot()

@bot.on_message
def handle_msg(ctx):
    # ctx.text 是用户发来的文字
    # ctx.reply 是快捷回复
    ctx.reply(f"收到！你刚才说：{ctx.text}")

# 启动！
if __name__ == "__main__":
    bot.start()
```

运行 `python bot.py`，然后在飞书里给机器人发句 "Hello"，它应该会秒回你。

---

## 第三步：让它听懂指令

除了复读，我们通常需要机器人执行特定指令。`LarkBot` 提供了类似 Flask 的路由装饰器。

```python
# 1. 精确指令：匹配 /help
@bot.command("/help")
def on_help(ctx):
    ctx.reply("我是智能助手，你可以问我任何问题，或者发送 /card 查看卡片演示。")

# 2. 正则匹配：比如匹配 "查询 xxx"
@bot.regex(r"^查询\s+(.+)$")
def on_query(ctx):
    # 提取正则分组
    keyword = ctx._match.group(1)
    ctx.reply(f"🔍 正在为你查询：{keyword}...")

# 3. 私聊兜底：只处理私聊，不干扰群聊
@bot.on_message(private_only=True)
def handle_private(ctx):
    ctx.reply("这是私聊专属服务 😘")
```

---

## 第四步：接入 AI 大脑 (ChatGPT)

这才是重头戏。我们想让机器人接入大模型，实现智能问答。
`chattool` 内置了 `ChatSession`，帮你管理多用户的对话历史（Memory）。

```python
from chattool.tools.lark import LarkBot, ChatSession

bot = LarkBot()
# 定义系统提示词 (System Prompt)
session = ChatSession(system="你是一个资深 Python 工程师，说话幽默风趣。")

@bot.on_message
def ai_chat(ctx):
    # session.chat 会自动区分不同用户 (ctx.sender_id)
    # 并在本地维护对话历史
    reply = session.chat(ctx.sender_id, ctx.text)
    ctx.reply(reply)

bot.start()
```

现在，你的机器人已经是一个能记住上下文的 AI 助手了！

> 进阶阅读：[AI 对话集成指南](../larkbot/ai-chat.md)

---

## 第五步：整点花活——交互式卡片

纯文字太干了？飞书的**卡片 (Interactive Cards)** 是神器。它可以包含按钮、图片、下拉框，甚至能像网页一样局部刷新。

### 发送一张带按钮的卡片

```python
@bot.command("/card")
def send_card(ctx):
    card = {
        "header": {"title": {"tag": "plain_text", "content": "待办事项"}, "template": "blue"},
        "elements": [
            {"tag": "div", "text": {"tag": "lark_md", "content": "**任务**：完成周报撰写"}},
            {
                "tag": "action",
                "actions": [
                    # 定义一个按钮，value 里藏着 action 名字
                    {"tag": "button", "text": {"tag": "plain_text", "content": "✅ 标记完成"}, "value": {"action": "done"}}
                ]
            }
        ]
    }
    bot.send_card(ctx.sender_id, "user_id", card)
```

### 处理按钮点击

用户点了按钮，我们需要给反馈。注意这里用 `@bot.card_action` 装饰器。

```python
@bot.card_action("done")
def on_card_done(ctx):
    # 1. 弹个窗提示用户
    ctx.toast("干得漂亮！任务已完成", type="success")
    
    # 2. 原地更新卡片，把标题变绿
    ctx.update_card({
        "header": {"title": {"tag": "plain_text", "content": "✅ 任务已完成"}, "template": "green"},
        "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": "操作人：User"}}]
    })
```

效果非常丝滑，完全不需要用户重新发消息。

> 进阶阅读：[交互卡片深度指南](../larkbot/cards.md)

---

## 第六步：不想写代码？试试 CLI

有时候我们只是想测试一下 token 对不对，或者临时发个通知。`chattool` 贴心地准备了命令行工具。

**1. 验证配置是否正确**
```bash
chattool lark info
```

**2. 命令行发消息**
```bash
chattool lark send rexwzh "老板，今晚不加班！"
```

**3. 一键启动 AI 机器人**
甚至连代码都不用写，直接在终端启动一个 AI 机器人：
```bash
chattool serve lark ai --system "你是一个翻译官，把我说的话翻译成英文"
```

> 进阶阅读：[命令行工具手册](../larkbot/cli.md)

---

## 总结

通过 `chattool`，我们把飞书机器人的开发门槛降到了最低：
1.  **配置**：环境变量搞定凭证。
2.  **开发**：装饰器路由，逻辑清晰。
3.  **智能**：内置 Session 管理，一行代码接 AI。
4.  **交互**：卡片回调极其简单。

如果你想在生产环境（服务器）部署，只需要把 `bot.start()` 改成 Webhook 模式即可（支持 Flask/FastAPI），具体可以参考 [接收消息与路由](../larkbot/receiving.md)。

**现在，去动手写一个属于你的飞书机器人吧！** 🚀
