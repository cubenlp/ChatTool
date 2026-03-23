# test_chattool_lark_troubleshoot_basic

测试目标 `chattool lark troubleshoot ...` 命令面的基础链路，先固定接口与真实测试场景，再实现 CLI。

## 元信息

- 命令：`chattool lark troubleshoot <command> [args]`
- 目的：定义飞书诊断 CLI 的第一阶段命令边界与真实测试路径。
- 标签：`cli`
- 前置条件：具备飞书凭证。
- 环境准备：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
- 回滚：通常为只读，无需回滚。

## 用例 1：执行总诊断

- 初始环境准备：
  - 飞书凭证可用。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark troubleshoot doctor`。
  2. 预期输出总体状态、机器人信息、必需 scopes 状态和诊断建议。

参考执行脚本（伪代码）：

```sh
chattool lark troubleshoot doctor
```

## 用例 2：检查权限

- 初始环境准备：
  - 飞书凭证可用。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark troubleshoot check-scopes`。
  2. 预期输出关键 scopes 的状态与缺失项。

参考执行脚本（伪代码）：

```sh
chattool lark troubleshoot check-scopes
```

## 用例 3：检查事件与卡片交互

- 初始环境准备：
  - 飞书后台已有对应配置。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool lark troubleshoot check-events`。
  2. 执行 `chattool lark troubleshoot check-card-action`。
  3. 预期输出事件订阅与卡片交互的检查结果。

参考执行脚本（伪代码）：

```sh
chattool lark troubleshoot check-events
chattool lark troubleshoot check-card-action
```

## 用例 4：导出权限诊断卡片

- 初始环境准备：
  - 飞书凭证可用。
  - 若要直接发送卡片，需配置 `FEISHU_DEFAULT_RECEIVER_ID` 或显式传入接收者。
- 相关文件：
  - `<tmp>/scope-check-card.json`

预期过程和结果：
  1. 执行 `chattool lark troubleshoot check-scopes --card-file <path>`。
  2. 预期输出 scopes 诊断结果，并把可发送的飞书卡片 JSON 写到指定文件。
  3. 若继续执行 `chattool lark troubleshoot check-scopes --send-card`，预期把该诊断卡片发给目标接收者。

参考执行脚本（伪代码）：

```sh
chattool lark troubleshoot check-scopes --card-file /tmp/scope-check-card.json
chattool lark troubleshoot check-scopes --send-card
```
