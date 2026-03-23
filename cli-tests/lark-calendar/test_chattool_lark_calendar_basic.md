# test_chattool_lark_calendar_basic

测试目标 `chattool lark calendar ...` 命令面的基础链路，先固定接口与真实测试场景，再实现 CLI。

## 元信息

- 命令：`chattool lark calendar <group> <command> [args]`
- 目的：定义飞书 Calendar CLI 的第一阶段命令边界与真实测试路径。
- 标签：`cli`
- 前置条件：具备飞书凭证与日历权限。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_TEST_USER_ID`
  - `FEISHU_TEST_USER_ID_TYPE`
- 回滚：删除测试日程。

## 用例 1：创建日程

- 初始环境准备：
  - 准备明确的开始和结束时间。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark calendar event create --summary "测试会议" --start <time> --end <time>`。
  2. 预期返回 `event_id` 和创建成功信息。

参考执行脚本（伪代码）：

```sh
chattool lark calendar event create --summary "测试会议" --start 2026-03-24T14:00:00+08:00 --end 2026-03-24T15:00:00+08:00
```

## 用例 2：查询时间范围内日程

- 初始环境准备：
  - 准备查询时间范围。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark calendar event list --start <time> --end <time>`。
  2. 预期返回该时间范围内的日程列表。

参考执行脚本（伪代码）：

```sh
chattool lark calendar event list --start 2026-03-24T00:00:00+08:00 --end 2026-03-24T23:59:59+08:00
```

## 用例 3：修改日程时间

- 初始环境准备：
  - 准备一个可修改的 `event_id`。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark calendar event patch <event_id> --start <time> --end <time>`。
  2. 预期返回更新时间成功。

参考执行脚本（伪代码）：

```sh
chattool lark calendar event patch <event_id> --start 2026-03-24T15:00:00+08:00 --end 2026-03-24T16:00:00+08:00
```

## 用例 4：回复邀请

- 初始环境准备：
  - 准备一个可回复的 `event_id`。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark calendar event reply <event_id> --status accept`。
  2. 预期返回回复成功。

参考执行脚本（伪代码）：

```sh
chattool lark calendar event reply <event_id> --status accept
```

## 用例 5：查询忙闲

- 初始环境准备：
  - 准备查询时间范围。
  - 准备用户列表 JSON。
- 相关文件：
  - `<tmp>/users.json`

预期过程和结果：
  1. 执行 `chattool lark calendar freebusy list --start <time> --end <time> --json <path>`。
  2. 预期返回忙闲结果。

参考执行脚本（伪代码）：

```sh
chattool lark calendar freebusy list --start 2026-03-24T09:00:00+08:00 --end 2026-03-24T18:00:00+08:00 --json /tmp/users.json
```
