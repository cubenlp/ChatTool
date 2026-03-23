# 飞书 Skill：输出与格式约束

这份文档不是独立 skill，而是补充 `chattool lark` 相关 CLI 的输出约束，尤其是：

- `chattool lark send --card`
- `chattool lark send --post`
- `chattool lark reply`
- 文档通知消息

## CLI 相关默认规则

- 回给用户的说明优先简洁、低仪式感
- 消息正文、卡片 JSON、post JSON 的业务输入都通过 CLI 参数或文件传入
- 不新增临时环境变量传正文、接收者、文件路径

## 卡片和富文本开发时要注意

- 如果卡片或富文本显示异常，先排查消息结构本身，再排查权限
- 飞书 Markdown 与通用 Markdown 并不完全一致
- 继续扩消息格式相关 CLI 时，先看 `lark-markdown-syntax.md`

## 当前与 CLI 直接相关的建议

- `send --card` 适合结构化展示
- `send --post` 适合富文本消息
- `reply` 适合做线程内简短确认
- `notify-doc` 适合把文档链接和摘要发给目标用户
