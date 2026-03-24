# test_chattool_lark_overview_zh

校对 `skills/feishu/guide/overview.zh.md` 与英文总览是否仍然表达同一套 CLI 入口和核心约束。

## 元信息

- 命令：`chattool lark`
- 目的：验证双语总览没有出现不同步的命令面或配置规则。
- 标签：`cli`, `doc-audit`
- 前置条件：`overview.md` 与 `overview.zh.md` 同步维护。
- 环境准备：
  - 无
- 回滚：无

## 用例 1：校对双语总览一致性

- 初始环境准备：
  - 同时打开 `overview.md` 和 `overview.zh.md`。
- 相关文件：
  - `skills/feishu/guide/overview.md`
  - `skills/feishu/guide/overview.zh.md`

预期过程和结果：
  1. 检查两份总览都以 `chattool lark` 为入口。
  2. 检查两份总览都覆盖相同的命令主线。
  3. 若命令或配置规则有变更，两份文档都应同步更新。

参考执行脚本（伪代码）：

```sh
sed -n '1,220p' skills/feishu/guide/overview.md
sed -n '1,220p' skills/feishu/guide/overview.zh.md
```

