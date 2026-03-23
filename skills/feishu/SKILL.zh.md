---
name: feishu
description: 优先使用 `chattool lark` 作为唯一飞书 CLI 入口；把本 skill 当作飞书入口索引，先走 CLI，再看当前目录下的专题文档，最后把能力补回可复用 CLI。
version: 0.3.0
---

# 飞书 Skill

这个 skill 是唯一的飞书入口索引。`SKILL.md` / `SKILL.zh.md` 主要负责路由；安装时会整目录拷贝，因此 `skills/feishu/` 下的 markdown 文件都应视作同一个技能包的一部分。

## 默认原则

- 先用 `chattool lark`，不要先写一次性 OpenAPI 脚本。
- 业务输入优先走 CLI 参数，不新增临时环境变量。
- 缺口如果具有复用价值，先补 `src/chattool/tools/lark/`。
- 本 skill 包负责 CLI 入口说明、能力地图、测试先行约束与执行指导。

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
- 规划中的专题命令组
  - `chattool lark bitable ...`
  - `chattool lark calendar ...`
  - `chattool lark im ...`
  - `chattool lark task ...`
  - `chattool lark troubleshoot ...`
- 本地调试
  - `chattool lark listen`
  - `chattool lark chat`

## 包内文档

- `setup-and-routing.md`
  - 凭证、`-e/--env`、默认接收者、测试账号变量、任务路由
- `messaging.md`
  - send / upload / reply / listen / chat
- `documents.md`
  - 文档命令、稳定正文轨、结构化 docx 轨
- `bitable.md`
  - `chattool lark bitable ...` 的目标命令面与测试设计
- `calendar.md`
  - `chattool lark calendar ...` 的目标命令面与测试设计
- `im-read.md`
  - `chattool lark im ...` 的目标命令面与真实消息读取场景
- `task.md`
  - `chattool lark task ...` 的目标命令面与任务/清单场景
- `troubleshoot.md`
  - `chattool lark troubleshoot ...` 的目标命令面与诊断场景
- `channel-rules.md`
  - `send`、`reply`、卡片、富文本、文档相关的飞书输出约束
- `api-reference.md`
  - 官方 API 文档 URL 与 CLI 到 API 的映射
- `official-docx-capabilities.md`
  - docx block 能力边界与当前实现范围
- `feishu-docx-adoption-notes.md`
  - 外部参考实现里哪些值得借鉴，哪些不应直接搬入
- `bitable-field-properties.md`
  - bitable 字段 property 结构参考
- `bitable-record-values.md`
  - bitable 记录值格式参考
- `bitable-examples.md`
  - 未来 `chattool lark bitable ...` 的场景示例
- `lark-markdown-syntax.md`
  - 飞书 Markdown 与卡片语法约束

## 路由规则

现在只有一个飞书 skill 目录：`skills/feishu/`。

- 不再把任务路由到 `feishu-*` 同级 skill 目录。
- 统一使用当前目录下的专题文档。
- 如果专题 CLI 还没实现，先写目标命令和 `cli-tests/*.md`，再做实现。

## 实施优先级

1. 先看现有 `chattool lark` 是否已经覆盖目标动作。
2. 如果没有，但能力可复用，先写目标 CLI 命令面和 `cli-tests/*.md`。
3. 命令边界稳定后，再补 CLI / 工具实现。
4. 超出当前覆盖范围时，先查 `api-reference.md` 和官方 Feishu 文档，再把结论沉淀回 ChatTool。
