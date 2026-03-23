---
name: feishu
description: 优先使用 `chattool lark` 处理飞书验证、消息发送、文档沉淀与本地调试；把本 skill 当作飞书入口索引，先走 CLI，再走专题文档，再把可复用能力补回 ChatTool。
version: 0.2.0
---

# 飞书 Skill

这个 skill 是飞书能力的入口索引。`SKILL.md` / `SKILL.zh.md` 主要负责路由；安装时会整目录拷贝，因此 `skills/feishu/` 下的文档都应视作同一个技能包的一部分。

## 默认原则

- 先用 `chattool lark`，不要先写一次性 OpenAPI 脚本。
- 业务输入优先走 CLI 参数，不新增临时环境变量。
- 缺口如果具有复用价值，先补 `src/chattool/tools/lark/`。
- 本 skill 包负责入口说明、能力地图、reference 与执行指导。

## 能力地图

- 验证与权限
  - `chattool lark info`
  - `chattool lark scopes`
- 消息与资源投递
  - `chattool lark send`
  - `chattool lark upload`
  - `chattool lark reply`
- 文档沉淀
  - 稳定正文轨：`chattool lark notify-doc`、`doc append-text`、`doc append-file`
  - 结构化 docx 轨：`chattool lark doc parse-md`、`doc append-json`
- 本地调试
  - `chattool lark listen`
  - `chattool lark chat`

## 包内文档

- `docs/setup-and-routing.md`
  - 凭证、`-e/--env`、默认接收者、测试账号变量、任务路由
- `docs/messaging.md`
  - send / upload / reply / listen / chat
- `docs/documents.md`
  - 文档命令、稳定正文轨、结构化 docx 轨
- `docs/api-reference.md`
  - 官方 API 文档 URL 与 CLI 到 API 的映射
- `docs/official-docx-capabilities.md`
  - docx block 能力边界与当前实现范围
- `docs/feishu-docx-adoption-notes.md`
  - 外部参考实现里哪些值得借鉴，哪些不应直接搬入

## 独立专题 Skill

- `feishu-bitable`
- `feishu-calendar`
- `feishu-im-read`
- `feishu-task`
- `feishu-troubleshoot`
- `feishu-channel-rules`

文档读写类旧 skill 已并回主 skill，不再作为单独入口维护。

## 实施优先级

1. 先看现有 `chattool lark` 是否已经覆盖目标动作。
2. 如果没有，但能力可复用，先补 CLI / 工具实现。
3. 命令边界稳定后，再更新本 skill 包与专题文档。
4. 超出当前覆盖范围时，先查 `docs/api-reference.md` 和官方 Feishu 文档，再把结论沉淀回 ChatTool。
