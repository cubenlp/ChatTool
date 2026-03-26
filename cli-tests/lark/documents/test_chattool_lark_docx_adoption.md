# test_chattool_lark_docx_adoption

校对 `skills/feishu/documents/feishu-docx-adoption-notes.md` 是否仍然准确描述 docx CLI 的采用策略。

## 元信息

- 命令：`chattool lark doc ...`
- 目的：验证 docx 采用说明与当前开发策略一致。
- 标签：`cli`, `doc-audit`
- 前置条件：文档能力按 doc-first 与双轨模型推进。
- 环境准备：
  - 无
- 回滚：无

## 用例 1：校对采用策略

- 初始环境准备：
  - 打开 `skills/feishu/documents/feishu-docx-adoption-notes.md`。
- 相关文件：
  - `skills/feishu/documents/feishu-docx-adoption-notes.md`

预期过程和结果：
  1. 检查文档是否仍强调先写 `cli-tests/lark/documents/*.md`，再补实现。
  2. 检查文档是否仍强调高频、稳定、可复用的能力优先进入 CLI。
  3. 检查文档是否仍把结构化能力限制在官方 block API 明确可行的范围内。

参考执行脚本（伪代码）：

```sh
sed -n '1,200p' skills/feishu/documents/feishu-docx-adoption-notes.md
```

