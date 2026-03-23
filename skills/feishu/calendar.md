# 飞书 Skill：Calendar CLI 规划

这份文档描述目标 `chattool lark calendar ...` 命令面，以及对应的测试设计方向。

## 目标入口

```bash
chattool lark calendar ...
```

## 当前已支持命令面

```bash
chattool lark calendar primary
chattool lark calendar event create --summary <text> --start <time> --end <time>
chattool lark calendar event list --start <time> --end <time>
chattool lark calendar event get <event_id>
chattool lark calendar event patch <event_id> ...
chattool lark calendar event reply <event_id> --status <accept|decline|tentative>
chattool lark calendar freebusy list --start <time> --end <time> [--json <users.json>]
```

## 后续规划命令面

### event

```bash
chattool lark calendar event search <query>
chattool lark calendar event instances <event_id> --start <time> --end <time>
```

### attendee

```bash
chattool lark calendar attendee list <calendar_id> <event_id>
chattool lark calendar attendee add <calendar_id> <event_id> --json <attendees.json>
chattool lark calendar attendee remove <calendar_id> <event_id> --json <user_ids.json>
```

## CLI 设计原则

- 当前先把 `primary / event / freebusy` 主线做稳
- 时间统一走明确的 CLI 参数，不通过临时环境变量传
- 复杂参会人列表用 JSON 文件承载
- 默认优先兼容 `user_id` 体系；如需切换再用 `--user-id-type`

## 真实测试要求

`cli-tests/lark-calendar/*.md` 至少覆盖：

- 创建日程
- 查询时间范围内日程
- 修改日程时间
- 回复邀请
- 查询忙闲

文档必须写清：

- 所需配置项：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_TEST_USER_ID`
  - `FEISHU_TEST_USER_ID_TYPE`
- 时间格式
- 回滚方式：
  - 删除测试日程

## 当前状态

- 这组命令已经落地 `primary`、`event` 基础链路和 `freebusy list`。
- `search`、`instances`、`attendee` 仍保留为后续项。
