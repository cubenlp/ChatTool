# 飞书 Skill：Bitable 记录值参考

这份文档保留为 `chattool lark bitable record ...` 后续开发参考，不作为单独入口。

## 使用方式

- 先用 `field list` 看字段类型
- 再按字段类型组织 record JSON
- 最后把 record payload 固化到 `cli-tests/lark-bitable/*.md`

## 高风险字段

- 人员：`[{\"id\": \"ou_xxx\"}]`
- 日期：毫秒时间戳
- 单选：字符串
- 多选：字符串数组
- 超链接：对象
- 附件：`[{\"file_token\": \"xxx\"}]`

这类结构不建议拆成大量零散 CLI 选项，优先允许 JSON 文件输入。
