# 飞书 Skill：Troubleshoot CLI 规划

这份文档描述目标 `chattool lark troubleshoot ...` 命令面，以及对应的测试设计方向。

## 目标入口

```bash
chattool lark troubleshoot ...
```

## 第一阶段目标命令面

```bash
chattool lark troubleshoot doctor
chattool lark troubleshoot check-scopes
chattool lark troubleshoot check-events
chattool lark troubleshoot check-card-action
```

其中 `check-scopes` 现在既可做终端诊断，也可导出或直接发送权限诊断卡片，便于把缺失分类发给应用维护者继续处理。

## 第一阶段主线

优先把 `doctor` 做成统一诊断入口，覆盖这些检查：

- 凭证是否可用
- 机器人是否激活
- 必需 scopes 是否存在
- 长连接 / 事件订阅是否配置齐
- 卡片交互是否具备回传条件

`check-scopes`、`check-events`、`check-card-action` 可作为后续分项命令。

## 真实测试要求

`cli-tests/lark-troubleshoot/*.md` 至少覆盖：

- `doctor` 基础诊断
- scopes 诊断
- 事件订阅链路检查

文档必须写清：

- 所需配置项：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
- 输出应包含哪些诊断项
- 回滚方式：
  - 通常为只读，无需回滚

## 当前状态

- 当前已落地 `doctor`、`check-scopes`、`check-events`、`check-card-action`。
- 旧 troubleshoot skill 中的 FAQ 与诊断思路继续吸收到 `doctor` 输出和后续分项诊断中。
