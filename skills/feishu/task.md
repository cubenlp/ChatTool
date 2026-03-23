# 飞书 Skill：Task CLI 规划

这份文档描述目标 `chattool lark task ...` 命令面，以及对应的测试设计方向。

## 目标入口

```bash
chattool lark task ...
```

## 当前已支持命令面

### task

```bash
chattool lark task get <task_guid>
chattool lark task create --summary <text>
chattool lark task patch <task_guid> ...
```

### tasklist

```bash
chattool lark task tasklist list
chattool lark task tasklist create <name>
chattool lark task tasklist get <tasklist_guid>
chattool lark task tasklist tasks <tasklist_guid>
chattool lark task tasklist add-members <tasklist_guid> --json <members.json>
```

## 凭证敏感命令

```bash
chattool lark task list
```

- `task list` 当前在 app/tenant 凭证下可能返回 token 类型错误。
- 这类报错应优先视为权限或 token 模式问题，而不是默认认为 CLI 参数有误。

## CLI 设计原则

- 用 `task` 和 `tasklist` 两级分组承载主要动作
- 成员、清单、截止时间等复杂结构优先走 JSON 输入或明确选项
- 时间统一走明确 CLI 参数
- 真实测试默认从配置对象读取测试用户

## 真实测试要求

`cli-tests/lark-task/*.md` 至少覆盖：

- 创建任务
- 查询未完成任务
- 更新任务状态
- 创建清单
- 查看清单任务

文档必须写清：

- 所需配置项：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_TEST_USER_ID`
  - `FEISHU_TEST_USER_ID_TYPE`
- 任务与清单 guid 的来源
- 回滚方式：
  - 删除测试任务
  - 删除测试清单

## 当前状态

- 当前已经落地 `task create/get/patch` 与 `tasklist create/list/get/tasks/add-members`。
- `task list` 目前保留命令入口，但需要结合当前凭证模式判断是否可用。
- 旧 task skill 中的约束和样例继续转为 CLI 参数与测试场景，不再作为独立 skill 入口。
