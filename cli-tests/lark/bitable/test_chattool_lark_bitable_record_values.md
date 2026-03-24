# test_chattool_lark_bitable_record_values

校对 `skills/feishu/bitable/references/record-values.md` 是否仍然和当前记录读写 CLI 预期一致。

## 元信息

- 命令：`chattool lark bitable record list|create|batch-create ...`
- 目的：验证记录值格式参考文档仍可指导 Bitable 记录类 CLI 使用与排障。
- 标签：`cli`, `doc-audit`
- 前置条件：Bitable 记录主线已实现。
- 环境准备：
  - 无
- 回滚：无

## 用例 1：校对记录值格式参考

- 初始环境准备：
  - 打开 `skills/feishu/bitable/references/record-values.md`。
- 相关文件：
  - `skills/feishu/bitable/references/record-values.md`

预期过程和结果：
  1. 检查文档是否仍面向记录读写 CLI 的值格式问题。
  2. 检查人员、日期、单选、多选、附件等高频类型是否仍有明确格式说明。
  3. 如果记录 CLI 的字段值约束变化，应同步更新这里的参考文档。

参考执行脚本（伪代码）：

```sh
sed -n '1,260p' skills/feishu/bitable/references/record-values.md
python -m chattool.client.main lark bitable record --help
```
