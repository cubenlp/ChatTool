# test_chattool_lark_bitable_basic

测试目标 `chattool lark bitable ...` 命令面的基础链路，先固定接口与真实测试场景，再实现 CLI。

## 元信息

- 命令：`chattool lark bitable <group> <command> [args]`
- 目的：定义飞书 Bitable CLI 的第一阶段命令边界与真实测试路径。
- 标签：`cli`
- 前置条件：具备飞书凭证与 Bitable 权限。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_TEST_USER_ID`
  - `FEISHU_TEST_USER_ID_TYPE`
- 回滚：删除测试 app / table / records。

## 用例 1：创建测试 app

- 初始环境准备：
  - 准备一个用于测试的名称。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark bitable app create "测试表格"`。
  2. 预期返回 `app_token`。
  3. 预期后续 table / field / record 命令可复用该 `app_token`。

参考执行脚本（伪代码）：

```sh
chattool lark bitable app create "测试表格"
```

## 用例 2：查看或创建数据表

- 初始环境准备：
  - 准备一个可用的 `app_token`。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark bitable table list <app_token>`。
  2. 如无合适测试表，可执行 `chattool lark bitable table create <app_token> "测试数据表"`。
  3. 预期返回 `table_id`。

参考执行脚本（伪代码）：

```sh
chattool lark bitable table list <app_token>
chattool lark bitable table create <app_token> "测试数据表"
```

## 用例 3：查看字段

- 初始环境准备：
  - 准备可访问的 `app_token` 和 `table_id`。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark bitable field list <app_token> <table_id>`。
  2. 预期返回字段列表与类型信息。

参考执行脚本（伪代码）：

```sh
chattool lark bitable field list <app_token> <table_id>
```

## 用例 4：新增记录

- 初始环境准备：
  - 准备一个可写的 `app_token` 和 `table_id`。
  - 准备 record JSON 文件。
- 相关文件：
  - `<tmp>/record.json`

预期过程和结果：
  1. 执行 `chattool lark bitable record create <app_token> <table_id> --json <path>`。
  2. 预期返回 `record_id`。

参考执行脚本（伪代码）：

```sh
chattool lark bitable record create <app_token> <table_id> --json /tmp/record.json
```

## 用例 5：批量创建记录

- 初始环境准备：
  - 准备一个可写的 `app_token` 和 `table_id`。
  - 准备 records JSON 文件。
- 相关文件：
  - `<tmp>/records.json`

预期过程和结果：
  1. 执行 `chattool lark bitable record batch-create <app_token> <table_id> --json <path>`。
  2. 预期返回创建成功与记录数。

参考执行脚本（伪代码）：

```sh
chattool lark bitable record batch-create <app_token> <table_id> --json /tmp/records.json
```
