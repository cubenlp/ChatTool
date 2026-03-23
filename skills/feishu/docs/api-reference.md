# 飞书 Skill：API Reference

这份文档只放“继续扩展 `chattool lark` 时最常查的官方入口”，不搬运整段 API 文档。

## 总入口

- 飞书开放平台应用页
  - `https://open.feishu.cn/app`
- 飞书开放平台文档首页
  - `https://open.feishu.cn/document/`

## CLI 到官方 API 的映射

### 验证与权限

- `chattool lark info`
  - 用途：验证应用凭证、确认机器人状态
  - 实现落点：`src/chattool/tools/lark/bot.py:get_bot_info`
  - 先查：应用配置页与机器人信息接口说明
- `chattool lark scopes`
  - 用途：查看当前应用已申请 / 已授权权限
  - 实现落点：`src/chattool/tools/lark/bot.py:get_scopes`
  - 先查：应用权限管理页与 scopes 相关文档

### 消息与资源

- `chattool lark send`
  - 发消息
  - 官方接口：`https://open.feishu.cn/document/server-docs/im-v1/message/create`
- `chattool lark reply`
  - 回复消息
  - 官方接口：`https://open.feishu.cn/document/server-docs/im-v1/message/reply`
- `chattool lark upload`
  - 上传图片
  - 官方接口：`https://open.feishu.cn/document/server-docs/im-v1/image/create`
- `chattool lark upload`
  - 上传文件
  - 官方接口：`https://open.feishu.cn/document/server-docs/im-v1/file/create`

### 云文档与 docx

- `chattool lark doc create`
  - 创建文档
  - 官方接口：`https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/create`
- `chattool lark doc append-json`
  - 追加结构化 block
  - 官方接口：`https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block/create`
- `chattool lark doc blocks`
  - 查看块结构
  - 先查：docx block children / get block 相关文档
- `chattool lark notify-doc`
  - 工作流命令，不是单一接口
  - 组合了 create document、append text、get meta、send message

## 扩展规则

1. 先确认目标动作是否应该成为 `chattool lark` 的稳定命令。
2. 再去查官方 API 文档，确认 payload 和权限要求。
3. 实现优先落到 `bot.py`、`docx_blocks.py`、`markdown_blocks.py`。
4. 命令边界稳定后，再更新 `skills/feishu/` 与用户文档。

## 当前建议优先级

- 稳定链路优先：消息发送、上传、回复、文档正文写入。
- 结构化增强其次：标题、列表、代码块、引用块、callout、divider。
- 不要把“临时脚本能做”当作最终形态；有复用价值的流程应尽快沉淀回 ChatTool CLI。
