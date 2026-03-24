# 飞书 Skill：云文档

飞书文档能力统一从 `chattool lark doc ...` 和 `chattool lark notify-doc` 出发说明。

## 双轨模型

### 稳定正文轨

- `chattool lark notify-doc`
- `chattool lark doc append-text`
- `chattool lark doc append-file`

目标：

- 优先保证正文能稳定写进去
- 适合日报、周报、会议纪要、任务总结

### 结构化 docx 轨

- `chattool lark doc parse-md`
- `chattool lark doc append-json`

目标：

- 面向标题、列表、代码块、引用块等结构化表达
- 能力边界以官方 docx block API 为准
- `append-json` 写入前会对部分 style 字段做安全归一化，避免不合法的代码语言字段直接导致整批 block 失败

## 当前已支持的主线命令

```bash
chattool lark notify-doc "日报" "今天完成了接口整理"
chattool lark doc create "周报草稿"
chattool lark doc get <document_id>
chattool lark doc raw <document_id>
chattool lark doc blocks <document_id>
chattool lark doc append-text <document_id> "今天完成了接口整理"
chattool lark doc append-file <document_id> ./daily.md
chattool lark doc parse-md ./daily.md -o ./daily.blocks.json
chattool lark doc append-json <document_id> ./daily.blocks.json
```

## 第一阶段命令边界

- `notify-doc`
  - 创建文档
  - 追加正文或文件
  - 获取文档链接
  - 发送链接给接收者
- `doc create|get|raw|blocks`
  - 做文档基本创建与查看
- `doc append-text|append-file`
  - 做稳定正文写入
- `doc parse-md|append-json`
  - 做结构化 block 的开发与调试

## 待开发但应继续沿当前主线扩展的能力

- `chattool lark doc update ...`
- `chattool lark doc delete-children ...`
- `chattool lark doc convert ...`
- drive/wiki 相关命令

这些后续能力仍应挂在 `chattool lark doc ...` 下，不再拆成独立 doc skill。

## 真实测试要求

文档相关 CLI 测试文档必须写清：

- 所需凭证和 docx 权限
- 所需配置项：
  - `FEISHU_APP_ID`
  - `FEISHU_APP_SECRET`
  - `FEISHU_DEFAULT_RECEIVER_ID`
- 默认优先复用 `FEISHU_DEFAULT_RECEIVER_ID` 作为通知目标
- 只有在需要隔离测试用户时，才额外引入：
  - `FEISHU_TEST_USER_ID`
  - `FEISHU_TEST_USER_ID_TYPE`
- 回滚方式：
  - 删除测试文档
  - 或明确说明保留测试痕迹

继续扩文档能力前，先看 `official-docx-capabilities.md`、`feishu-docx-adoption-notes.md` 和 `../guide/api-reference.md`。
