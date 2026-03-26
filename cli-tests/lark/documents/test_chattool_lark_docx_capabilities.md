# test_chattool_lark_docx_capabilities

校对 `skills/feishu/documents/official-docx-capabilities.md` 是否仍然准确描述当前 docx 主线边界。

## 元信息

- 命令：`chattool lark doc ...`
- 目的：验证 docx 能力边界文档和当前实现的命令面保持一致。
- 标签：`cli`, `doc-audit`
- 前置条件：文档主线命令已实现。
- 环境准备：
  - 无
- 回滚：无

## 用例 1：校对双轨边界

- 初始环境准备：
  - 打开 `skills/feishu/documents/official-docx-capabilities.md`。
- 相关文件：
  - `skills/feishu/documents/official-docx-capabilities.md`

预期过程和结果：
  1. 检查文档是否仍区分稳定正文轨与结构化 docx 轨。
  2. 检查文档是否仍覆盖 `create`、`get`、`raw`、`blocks`、`append-text`、`append-file`、`parse-md`、`append-json`。
  3. 检查扩展建议是否仍指向 `cli-tests/lark/documents/*.md`。

参考执行脚本（伪代码）：

```sh
sed -n '1,200p' skills/feishu/documents/official-docx-capabilities.md
python -m chattool.client.main lark doc --help
```

