# test_chattool_lark_bitable_field_properties

校对 `skills/feishu/bitable/references/field-properties.md` 是否仍然和当前字段创建/更新 CLI 预期一致。

## 元信息

- 命令：`chattool lark bitable field create ...`
- 目的：验证字段 property 参考文档仍可指导 Bitable CLI 扩展与排障。
- 标签：`cli`, `doc-audit`
- 前置条件：Bitable 字段主线已实现。
- 环境准备：
  - 无
- 回滚：无

## 用例 1：校对字段 property 参考

- 初始环境准备：
  - 打开 `skills/feishu/bitable/references/field-properties.md`。
- 相关文件：
  - `skills/feishu/bitable/references/field-properties.md`

预期过程和结果：
  1. 检查文档是否仍面向 `field create` 这类 CLI 场景。
  2. 检查文档是否仍按字段类型说明 `property` 结构，而不是孤立 API 片段。
  3. 如果字段 CLI 支持面变化，应同步更新这里的 property 说明。

参考执行脚本（伪代码）：

```sh
sed -n '1,260p' skills/feishu/bitable/references/field-properties.md
python -m chattool.client.main lark bitable field --help
```

