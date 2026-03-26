# test_chattool_lark_api_reference

校对 `skills/feishu/guide/api-reference.md` 是否仍然覆盖当前 CLI 主线到官方 API 的实用映射。

## 元信息

- 命令：`chattool lark`
- 目的：验证 API reference 没有遗漏当前 CLI 主线，也没有指向错误的能力边界。
- 标签：`cli`, `doc-audit`
- 前置条件：飞书 CLI 主线已经收口。
- 环境准备：
  - 无
- 回滚：无

## 用例 1：校对主线命令到 API 的映射

- 初始环境准备：
  - 打开 `skills/feishu/guide/api-reference.md`。
- 相关文件：
  - `skills/feishu/guide/api-reference.md`

预期过程和结果：
  1. 检查 `info`、`scopes`、`send`、`reply`、`upload` 是否都有官方 API 链接。
  2. 检查 `notify-doc` 与 `doc create|get|raw|blocks|append-text|append-file|parse-md|append-json` 是否都有对应的 docx API 索引。
  3. 检查 `doc perm-public-get|perm-public-set|perm-member-list|perm-member-add` 是否已有对应的 drive 权限 API 链接。
  4. 检查 `bitable`、`calendar`、`im`、`task` 是否仍被列为后续专题 CLI。

参考执行脚本（伪代码）：

```sh
sed -n '1,220p' skills/feishu/guide/api-reference.md
python -m chattool.client.main lark --help
```
