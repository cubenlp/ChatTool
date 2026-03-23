# 飞书 Skill：Bitable CLI 场景示例

这份文档用于帮助后续把 bitable 场景写进 `cli-tests/lark-bitable/*.md` 和 CLI 示例。

## 推荐优先覆盖的场景

1. 创建 app 和 table
2. 查看字段类型
3. 批量导入记录
4. 更新单条记录
5. 删除空行或批量删除记录

## 编写测试时的建议

- 使用临时 app 或隔离表，避免污染真实业务表
- 记录 `app_token`、`table_id`、`record_id` 的来源
- 文档里明确回滚步骤
