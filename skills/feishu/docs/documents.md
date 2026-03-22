# 飞书 Skill：云文档

## 适用场景

- 把日报、周报、会议纪要、任务总结沉淀到飞书文档。
- 先生成文档，再把链接发给自己或指定用户。
- 把本地整理好的 `txt/md` 文件稳定写入飞书文档。

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
- `.md` 会先转换成飞书兼容的纯文本段落，再写入文档。
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
- 如果后续需要更新块、删除块、Drive/Wiki 目录操作，可以沿着 `chattool lark doc ...` 继续补。
