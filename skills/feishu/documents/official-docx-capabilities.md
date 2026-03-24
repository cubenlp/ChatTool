# 飞书 Skill：官方 docx 能力边界

这份文档服务于 `chattool lark doc ...` 开发，不是用户入口教程。

## 当前主线边界

当前主线优先覆盖：

- 创建文档
- 获取文档
- 获取纯文本
- 查看 block 列表
- 追加纯文本
- 追加文件内容
- 解析 Markdown 为 block JSON
- 追加 block JSON

## 当前双轨

- 稳定正文轨
  - `notify-doc`
  - `doc append-text`
  - `doc append-file`
- 结构化 docx 轨
  - `doc parse-md`
  - `doc append-json`

## 开发约束

- 结构化能力扩展时，优先补 `docx_blocks.py` 和 `markdown_blocks.py`
- 稳定正文轨优先保证成功写入，不追求完整 Markdown 还原
- 结构化 docx 轨应以官方 block 能力为准，不擅自承诺未支持块类型

## 继续扩展前要确认

- 当前 block 类型是否被官方接口支持
- 新块是否适合进入稳定正文轨
- 新块是否需要单独的 `cli-tests/lark/documents/*.md` 场景覆盖
