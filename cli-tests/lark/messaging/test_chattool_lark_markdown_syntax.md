# test_chattool_lark_markdown_syntax

校对 `skills/feishu/messaging/lark-markdown-syntax.md` 是否仍然覆盖当前卡片/富文本相关 CLI 场景所需的 Markdown 语法边界。

## 元信息

- 命令：`chattool lark send --card`、`chattool lark send --post`、`chattool lark reply`
- 目的：验证 Markdown 语法参考仍可作为消息类 CLI 的参考边界。
- 标签：`cli`, `doc-audit`
- 前置条件：消息卡片与富文本能力仍使用飞书 Markdown 约束。
- 环境准备：
  - 无
- 回滚：无

## 用例 1：校对语法参考与 CLI 场景

- 初始环境准备：
  - 打开 `skills/feishu/messaging/lark-markdown-syntax.md`。
- 相关文件：
  - `skills/feishu/messaging/lark-markdown-syntax.md`

预期过程和结果：
  1. 检查文档是否仍覆盖卡片和富文本常用语法，例如链接、列表、代码块、标签、图片。
  2. 检查文档是否仍明确指出飞书 Markdown 与标准 Markdown 的差异。
  3. 如果 `send --card` 或 `send --post` 支持面变化，应同步修正文档。

参考执行脚本（伪代码）：

```sh
sed -n '1,260p' skills/feishu/messaging/lark-markdown-syntax.md
```

