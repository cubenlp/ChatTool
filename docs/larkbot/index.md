# 飞书机器人开发指南

基于 `chattool` + `lark-oapi` 构建飞书/Lark 智能机器人的完整文档。

## 快速导航

<div class="grid cards" markdown>

- :material-rocket-launch: **[快速开始](quickstart.md)**

    5 分钟发出第一条消息

- :material-cog: **[飞书平台配置](feishu-setup.md)**

    应用创建、权限申请、事件订阅

- :material-message-text: **[消息发送](messaging.md)**

    文本、富文本、卡片、文件

- :material-forum: **[接收消息与路由](receiving.md)**

    事件处理、指令路由、WebSocket 模式

- :material-robot: **[AI 对话集成](ai-chat.md)**

    接入 LLM、多用户会话管理

- :material-card-bulleted: **[交互卡片](cards.md)**

    卡片构建、按钮回调、动态更新

- :material-console: **[命令行工具](cli.md)**

    `chattool lark` / `chattool serve lark`

</div>

---

## 什么是飞书机器人

飞书机器人（Bot）是飞书开放平台提供的一种应用能力，可以与用户单聊、在群聊中响应消息，并通过 API 调用企业全域的服务。

将 `chattool` 的大语言模型能力与飞书机器人结合，可以快速构建：

- **AI 对话助手**：每个用户独立会话，支持多轮对话
- **审批通知机器人**：发送卡片，处理按钮回调
- **监控告警推送**：向指定群/人员推送结构化通知
- **工作流自动化**：结合日历、多维表格、审批流程

## 模块架构

```
chattool.tools.lark
├── LarkBot         # 核心机器人类（发送/接收/路由）
├── MessageContext  # 消息上下文，封装 ctx.reply() 等快捷操作
└── ChatSession     # 多用户 LLM 会话管理器
```

## 安装

```bash
pip install "chattool[tools]"
# 或单独安装 lark-oapi
pip install lark-oapi
```

## 最简示例

```python
from chattool.tools.lark import LarkBot

bot = LarkBot()  # 从环境变量读取凭证

@bot.on_message
def handle(ctx):
    ctx.reply(f"你说了：{ctx.text}")

bot.start()  # WebSocket 长连接，本地开发无需公网 URL
```
