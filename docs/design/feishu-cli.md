# ChatTool Feishu 设计

> 说明：这份文档现在只保留当前边界说明，不再维护旧版“大而全 `chattool lark`”设计。

## 当前默认路线

- 飞书 / Lark 自动化默认优先使用官方 `lark-cli`
- ChatTool 内的 `skills/feishu/` 只保留紧凑入口文档 `SKILL.md` / `SKILL.zh.md`，把使用者路由到上游 CLI 和仓库内教程
- `chattool setup lark-cli` 负责安装官方 CLI，并复用 ChatTool 现有的 Feishu 配置

## `chattool lark` 的当前边界

`chattool lark` 现在只保留 3 个最小辅助命令：

- `chattool lark info`
- `chattool lark send`
- `chattool lark chat`

保留理由：

- `info`
  - 用当前 ChatTool Feishu 配置做最短凭证验活
- `send`
  - 提供最小文本消息调试路径
- `chat`
  - 复用 ChatTool 本地会话能力调提示词

## 明确不再承担的能力

这些都不再由 `chattool lark` 承担：

- 文档创建 / 更新 / 搜索
- reply / listen / scopes / troubleshoot
- calendar / task / bitable / im / drive / sheets
- 其他对飞书 OpenAPI 的广覆盖 CLI 映射

原因：

- 官方 `lark-cli` 已经覆盖这条路线
- 这些能力继续留在 ChatTool 内部会形成一套重复维护的平行 CLI
- 对 ChatTool 来说，最有价值的是“配置复用”和“最短调试链路”，不是再维护一套飞书全量命令面

## 迁移原则

如果后续还要处理飞书需求，优先顺序应固定为：

1. 判断官方 `lark-cli` 是否已经覆盖
2. 如果只是安装 / 配置迁移问题，优先扩 `chattool setup lark-cli`
3. 如果只是最短调试需求，再考虑是否值得进入 `chattool lark`

默认不再往 `chattool lark` 里追加新的飞书域命令。
