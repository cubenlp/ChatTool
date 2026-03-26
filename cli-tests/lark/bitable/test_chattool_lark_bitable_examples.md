# test_chattool_lark_bitable_examples

校对 `skills/feishu/bitable/references/examples.md` 是否仍然能作为当前 Bitable CLI 的场景参考。

## 元信息

- 命令：`chattool lark bitable ...`
- 目的：验证 examples 参考文档与当前 Bitable CLI 主线保持一致。
- 标签：`cli`, `doc-audit`
- 前置条件：Bitable 主线命令已实现。
- 环境准备：
  - 无
- 回滚：无

## 用例 1：校对 examples 与 CLI 命令面

- 初始环境准备：
  - 打开 `skills/feishu/bitable/references/examples.md`。
- 相关文件：
  - `skills/feishu/bitable/references/examples.md`

预期过程和结果：
  1. 检查 examples 中的主场景是否仍可映射到 `app create`、`table list/create`、`field list/create`、`record list/create/batch-create`。
  2. 如果 examples 依赖当前尚未实现的 CLI，应明确标注为扩展目标，而不是已支持。
  3. 若 Bitable 主线命令扩展，examples 应同步补充。

参考执行脚本（伪代码）：

```sh
sed -n '1,260p' skills/feishu/bitable/references/examples.md
python -m chattool.client.main lark bitable --help
```

