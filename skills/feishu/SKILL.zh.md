---
name: feishu
description: 优先使用 `chattool lark` 处理飞书机器人验证、消息发送、文档沉淀与本地调试；业务输入走 CLI 参数，缺口优先补到 ChatTool。
---

# 飞书 Skill

这个 skill 的默认原则很简单：先用 `chattool lark`，不要先写一次性 OpenAPI 脚本。

## 目标

- 验证飞书机器人凭证、激活状态和权限范围。
- 完成文本、文件、卡片、富文本、引用回复等常见消息动作。
- 将文本或本地 `txt/md` 文件写入飞书云文档，并把链接通知给目标用户。
- 在终端中调试监听链路和 AI 对话链路。

## 路由规则

1. 飞书相关任务优先映射到 `chattool lark`。
2. 接收者、消息内容、文件路径、文档标题等业务输入直接走 CLI 参数。
3. 不要为一次性业务输入新增环境变量，避免和其他入口混淆。
4. 如果 CLI 不覆盖且能力可复用，先补 `src/chattool/tools/lark/`，再更新 skill。
5. 复杂流程拆到专题文档，`SKILL.md` / `SKILL.zh.md` 只保留总览、入口和路由规则。

## 常用命令

```bash
chattool lark info
chattool lark scopes -f im
chattool lark send <receiver> "你好"
chattool lark upload ./report.pdf
chattool lark reply <message_id> "收到"
chattool lark doc create "周报草稿"
chattool lark doc append-file <document_id> ./weekly.md
chattool lark notify-doc "周报草稿" --append-file ./weekly.md
chattool lark listen -l DEBUG
chattool lark chat --system "你是一名飞书助手"
```

## 专题文档

- `docs/setup-and-routing.md`：凭证、`-e/--env`、默认接收者和路由原则。
- `docs/messaging.md`：消息发送、资源上传、回复、监听、本地 chat 调试。
- `docs/documents.md`：飞书文档创建、查询、追加文本、追加文件、通知发送。
- `docs/official-docx-capabilities.md`：基于飞书官方 API 的 docx 块能力盘点与实现边界。

## 当前文档能力边界

- `chattool lark doc append-file` 当前更适合“从本地文件提取段落再追加”，不是完整 Markdown 渲染。
- `chattool lark notify-doc --append-file` 适合创建文档、写正文并发送链接。
- 飞书官方 `docx` 还支持标题、列表、代码块、引用块、callout 等结构化块，但 CLI 还没有完整暴露。
- 结构化块能力应以官方 API 文档为准，后续优先补块级接口，不继续堆启发式格式转换。
