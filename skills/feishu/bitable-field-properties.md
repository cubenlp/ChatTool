# 飞书 Skill：Bitable 字段 Property 参考

这份文档保留为 `chattool lark bitable field ...` 后续开发参考，不作为单独入口。

## 使用方式

- 先确定目标 CLI 子命令
- 再根据字段类型查对应 `property` 结构
- 最后把字段 payload 固化到测试文档和 CLI 输入样例

## 常见字段类型

- `type=1` 文本
- `type=2` 数字 / 进度 / 货币 / 评分
- `type=3` 单选
- `type=4` 多选
- `type=5` 日期
- `type=11` 人员
- `type=15` 超链接
- `type=17` 附件

继续实现前，优先参考官方 bitable 文档和 `bitable-examples.md` 中的场景。
