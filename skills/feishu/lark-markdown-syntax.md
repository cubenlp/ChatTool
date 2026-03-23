# 飞书 Skill：Markdown 与卡片语法参考

这份文档用于开发 `chattool lark send --card`、`--post` 等消息能力时做格式校对。

## 使用规则

- 如果消息需要飞书 Markdown，而不是普通 Markdown，先查这里
- 如果卡片显示异常，先确认语法边界，再排查权限或 payload

## 重点提醒

- 飞书 Markdown 与标准 Markdown 不完全一致
- 部分标题层级和嵌套语法有限制
- 图片、@人、代码块、彩色文本都有自己的写法

继续扩消息格式能力前，也应同步把这些约束写入测试文档和示例 JSON。
