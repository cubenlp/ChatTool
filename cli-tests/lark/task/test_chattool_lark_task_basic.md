# test_chattool_lark_task_basic

测试目标 `chattool lark task ...` 命令面的基础链路，先固定接口与真实测试场景，再实现 CLI。

## 元信息

- 命令：`chattool lark task <group> <command> [args]`
- 目的：定义飞书 Task CLI 的第一阶段命令边界与真实测试路径。
- 标签：`cli`
- 前置条件：具备飞书凭证与任务权限。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_TEST_USER_ID`
  - `FEISHU_TEST_USER_ID_TYPE`
- 回滚：删除测试任务与测试清单。

## 用例 1：创建任务

- 初始环境准备：
  - 准备任务标题。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark task create --summary "测试任务"`。
  2. 预期返回 `task_guid`。

参考执行脚本（伪代码）：

```sh
chattool lark task create --summary "测试任务"
```

## 用例 2：查询未完成任务

- 初始环境准备：
  - 无
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark task list`。
  2. 若当前凭证模式支持列表接口，预期返回当前可见任务列表。
  3. 若当前凭证模式不支持，CLI 至少应明确标记为权限或 token 类型问题，而不是静默失败。

参考执行脚本（伪代码）：

```sh
chattool lark task list
```

## 用例 3：更新任务状态

- 初始环境准备：
  - 准备可更新的 `task_guid`。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark task patch <task_guid> --completed-at <time>`。
  2. 预期返回更新成功。

参考执行脚本（伪代码）：

```sh
chattool lark task patch <task_guid> --completed-at 2026-03-24T15:00:00+08:00
```

## 用例 4：创建清单

- 初始环境准备：
  - 准备清单名称。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark task tasklist create "测试清单"`。
  2. 预期返回 `tasklist_guid`。

参考执行脚本（伪代码）：

```sh
chattool lark task tasklist create "测试清单"
```

## 用例 5：查看清单任务

- 初始环境准备：
  - 准备 `tasklist_guid`。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark task tasklist tasks <tasklist_guid>`。
  2. 预期返回清单中的任务列表。

参考执行脚本（伪代码）：

```sh
chattool lark task tasklist tasks <tasklist_guid>
```

## 备注

- `task list` 是否可用，受当前飞书凭证模式影响。
- 当前仓库默认以 app/tenant 凭证为主，若接口返回 token 类型相关错误，应在文档和诊断输出中标记为权限问题。
