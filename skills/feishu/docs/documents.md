# 飞书 Skill：云文档

## 适用场景

- 把日报、周报、会议纪要、任务总结沉淀到飞书文档。
- 先生成文档，再把链接发给自己或指定用户。
- 把本地整理好的 `txt/md` 文件稳定写入飞书文档。

## 双轨模型

飞书文档相关能力统一分成两条轨道：

### 稳定正文轨

- `chattool lark notify-doc`
- `chattool lark doc append-text`
- `chattool lark doc append-file`

这条轨道优先保证“能稳定写进去”，适合日报、周报、纪要等正文沉淀。

### 结构化 docx 轨

- `chattool lark doc parse-md`
- `chattool lark doc append-json`

这条轨道面向标题、列表、代码块、引用块等结构化表达。能力边界以官方 docx block API 为准。

## 基础命令

```bash
chattool lark doc create "周报草稿"
chattool lark doc get <document_id>
chattool lark doc raw <document_id>
chattool lark doc blocks <document_id>
chattool lark doc append-text <document_id> "今天完成了接口整理"
```

## 从文件追加正文

```bash
chattool lark doc parse-md ./daily.md
chattool lark doc parse-md ./daily.md -o ./daily.blocks.json
chattool lark doc append-json <document_id> ./daily.blocks.json
chattool lark doc append-file <document_id> ./daily.txt
chattool lark doc append-file <document_id> ./daily.md
chattool lark doc append-file <document_id> ./daily.md --batch-size 10
```

说明：

- `parse-md` 会先把 Markdown 转换为飞书 docx block JSON，方便检查结构映射。
- `append-json` 会直接把结构化 block JSON 写入飞书文档。
- `.txt` 按非空行切成段落。
- `.md` 在 `append-file` 这条命令上会先转换成飞书兼容的纯文本段落，再写入文档。
- 批量写入失败时，会自动降级到单段写入。

## 创建文档并发通知

```bash
chattool lark notify-doc "日报" "今天完成了接口整理"
chattool lark notify-doc "日报" --append-file ./daily.md
chattool lark notify-doc "日报" --append-file ./daily.md --receiver f25gc16d
chattool lark notify-doc "日报" --append-file ./daily.md --batch-size 10
chattool lark notify-doc "日报" --append-file ./daily.md --open
```

这条命令会：

1. 创建文档。
2. 追加正文或文件内容。
3. 获取文档链接。
4. 将链接发送给目标接收者。

## 当前边界

- 这一层主要覆盖文档创建、读取、查看块、追加文本和追加文件。
- `append-file` 的定位是“文件转正文段落追加”，不是完整 Markdown 渲染。
- 如果后续需要块级更新、删除块、Drive/Wiki 目录操作，可以沿着 `chattool lark doc ...` 继续补。
- 要继续扩块级能力，先看 `docs/official-docx-capabilities.md` 和 `docs/api-reference.md`。
