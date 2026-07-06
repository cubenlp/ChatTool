# ChatTool Feishu / Lark 设计

> 说明：Lark bot helper 已从 ChatTool 迁移到独立 `ChatLark`。这份文档只保留当前边界说明。

## 当前默认路线

- 飞书 / Lark bot helper 使用独立 `ChatLark` / `chatlark`。
- 广覆盖飞书 OpenAPI 自动化默认优先使用官方 `lark-cli`。
- `chatup lark-cli` 负责安装官方 CLI，并复用 ChatEnv / Feishu 配置。
- ChatTool 不再 re-export `FeishuConfig`；Feishu typed env schema 由 `chatenv.configs.FeishuConfig` 提供。

## ChatLark 边界

ChatLark 承接从 ChatTool 移出的常规 bot helper 能力：

- `LarkBot`
- `MessageContext`
- message payload helpers
- markdown/docx block helpers
- `chatlark info`
- `chatlark send`
- `chatlark serve echo`
- `chatlark serve webhook`

模型调用相关入口暂不接回 ChatTool；如后续要做 AI chat bot，应在 ChatLark 侧单独设计模型 backend 边界。

## ChatTool 不再承担的能力

这些都不再由 ChatTool 承担：

- `chattool lark`
- `chattool serve lark`
- parent-owned `src/chattool/tools/lark/`
- parent-owned `src/chattool/serve/lark_serve.py`
- 文档创建 / 更新 / 搜索等广覆盖 OpenAPI CLI 映射
- reply / listen / scopes / troubleshoot 等 Lark 专属调试命令
- calendar / task / bitable / im / drive / sheets 等 OpenAPI 分域命令

原因：

- 常规 bot helper 已有独立 `ChatLark`。
- 广覆盖 OpenAPI 路线已有官方 `lark-cli`。
- ChatTool 继续保留 Lark 业务实现会形成重复维护的平行 CLI。

## 后续原则

如果后续还要处理飞书 / Lark 需求，优先顺序固定为：

1. 判断 `ChatLark` 是否应该承接 bot helper 能力。
2. 判断官方 `lark-cli` 是否已经覆盖广泛 OpenAPI 操作。
3. 如果只是安装 / 配置迁移问题，优先扩 `chatup lark-cli` 或 ChatEnv。
4. 默认不再往 ChatTool parent 中添加新的 Lark 业务实现。
