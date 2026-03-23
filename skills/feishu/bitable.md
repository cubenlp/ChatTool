# 飞书 Skill：Bitable CLI 规划

这份文档描述目标 `chattool lark bitable ...` 命令面，以及对应的测试设计方向。当前重点是先定接口和测试，不先保留旧工具式写法。

## 目标入口

```bash
chattool lark bitable ...
```

## 当前已支持命令面

### app

```bash
chattool lark bitable app create <name>
```

### table

```bash
chattool lark bitable table list <app_token>
chattool lark bitable table create <app_token> <name>
```

### field

```bash
chattool lark bitable field list <app_token> <table_id>
chattool lark bitable field create <app_token> <table_id> <field_name> --type <type>
```

### record

```bash
chattool lark bitable record list <app_token> <table_id>
chattool lark bitable record create <app_token> <table_id> --json <record.json>
chattool lark bitable record batch-create <app_token> <table_id> --json <records.json>
```

## 后续规划命令面

```bash
chattool lark bitable app get <app_token>
chattool lark bitable field update <app_token> <table_id> <field_id> ...
chattool lark bitable record update <app_token> <table_id> <record_id> --json <record.json>
chattool lark bitable record batch-delete <app_token> <table_id> --json <record_ids.json>
```

## CLI 设计原则

- 先按用户动作分组：`app / table / field / record`
- 复杂字段结构和记录值格式放 JSON 文件输入，不把巨大 payload 塞成长参数串
- 字段 property 和记录值格式查这几个参考文档：
  - `bitable-field-properties.md`
  - `bitable-record-values.md`
  - `bitable-examples.md`

## 真实测试要求

`cli-tests/lark-bitable/*.md` 至少覆盖：

- 创建 app
- 创建或查看 table
- 列出字段
- 新增一条 record
- 批量写入 record

文档必须写清：

- 所需配置项：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_TEST_USER_ID`
  - `FEISHU_TEST_USER_ID_TYPE`
- 临时资源：
  - `app_token`
  - `table_id`
- 回滚方式：
  - 删除测试 app / table / records

## 当前状态

- 这组命令已经落地 `app create`、`table list/create`、`field list/create`、`record list/create/batch-create`。
- 更新、删除、按 token 获取资源等操作继续保留为后续项。
