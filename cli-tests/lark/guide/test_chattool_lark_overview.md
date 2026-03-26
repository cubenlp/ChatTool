# test_chattool_lark_overview

校对 `skills/feishu/guide/overview.md` 是否仍然准确描述飞书 CLI 的总览、入口与最小命令面。

## 元信息

- 命令：`chattool lark info|scopes|send|upload|reply|listen|chat|doc ...`
- 目的：验证总览文档与当前 CLI 主线保持一致。
- 标签：`cli`, `doc-audit`
- 前置条件：飞书主线命令已实现。
- 环境准备：
  - 无
- 回滚：无

## 用例 1：校对主命令面

- 初始环境准备：
  - 打开 `skills/feishu/guide/overview.md`。
- 相关文件：
  - `skills/feishu/guide/overview.md`

预期过程和结果：
  1. 检查总览中是否仍以 `chattool lark` 为总入口。
  2. 检查命令清单是否覆盖 `info`、`scopes`、`send`、`upload`、`reply`、`listen`、`chat`、`doc ...`。
  3. 检查文档是否仍强调默认接收者优先使用 `FEISHU_DEFAULT_RECEIVER_ID`。

参考执行脚本（伪代码）：

```sh
sed -n '1,220p' skills/feishu/guide/overview.md
python -m chattool.client.main lark --help
```

