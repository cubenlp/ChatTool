# test_chattool_lark_channel_rules

校对 `skills/feishu/messaging/channel-rules.md` 是否仍然和当前 CLI 输出策略一致。

## 元信息

- 命令：`chattool lark send`、`chattool lark reply`、`chattool lark notify-doc`
- 目的：验证消息输出规则文档仍能指导 CLI 输出与卡片/富文本写法。
- 标签：`cli`, `doc-audit`
- 前置条件：消息与文档通知命令已实现。
- 环境准备：
  - 无
- 回滚：无

## 用例 1：校对输出规则与命令面

- 初始环境准备：
  - 打开 `skills/feishu/messaging/channel-rules.md`。
- 相关文件：
  - `skills/feishu/messaging/channel-rules.md`

预期过程和结果：
  1. 检查文档是否仍指向 `send`、`reply`、`notify-doc` 与 `doc ...`。
  2. 检查文档是否仍强调简洁、低仪式感的输出风格。
  3. 若消息格式支持发生变化，应同步更新这里的规则说明。

参考执行脚本（伪代码）：

```sh
sed -n '1,200p' skills/feishu/messaging/channel-rules.md
```

