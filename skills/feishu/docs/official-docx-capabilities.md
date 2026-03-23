# 飞书 Skill：官方 Docx 能力盘点

这份文档只做一件事：基于飞书官方 `docx` API 文档与 SDK 类型，整理目前可以稳定依赖的块能力，并对照 ChatTool 当前实现，避免继续把飞书文档能力做偏。

## 官方文档入口

- 创建文档：
  `https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/create?lang=zh-CN`
- 创建块：
  `https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block/create?lang=zh-CN`
- 官方 Markdown 版：
  `https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document/create.md`
  `https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block/create.md`

## 已确认的块能力

根据官方 `document-block/create.md`，创建块接口不是只能写纯文本，而是支持大量结构化块。当前和 ChatTool 最近需求直接相关的有：

- 文本 Block：`block_type=2`
- 标题 1-9 Block：`block_type=3..11`
- 无序列表 Block：`block_type=12`
- 有序列表 Block：`block_type=13`
- 代码块 Block：`block_type=14`
- 引用 Block：`block_type=15`
- 待办事项 Block：`block_type=17`
- 高亮块 Block：`block_type=19`
- 分割线 Block：`block_type=22`

此外，SDK `lark_oapi.api.docx.v1.BlockBuilder` 暴露的构造方法也能对应印证这些能力：

- `text(...)`
- `heading1(...)` 到 `heading9(...)`
- `bullet(...)`
- `ordered(...)`
- `code(...)`
- `quote(...)`
- `callout(...)`
- `divider(...)`

## 当前实现偏差

最近为了先把文档发出去，ChatTool 这条链路做了一个“把 Markdown 整理成纯文本段落”的实现。这个方向有两个问题：

1. 它把飞书原生支持的结构化块降级成普通文本。
2. 它会让技能层和 CLI 层误导用户，以为飞书文档只能接受“处理后的纯文本段落”。

这和官方能力边界不一致。

## 当前应如何收敛

现阶段更合理的收敛方式是：

### 1. 把能力分层说清楚

- `append-text`：稳定纯文本追加。
- `append-file`：如果继续保留，默认语义应该是“文件转段落追加”，不要伪装成完整 Markdown 渲染。
- 新的结构化写入能力：单独设计，不要偷偷塞进 `append-file`。

### 2. 先支持一组明确的结构块

如果继续增强 `chattool lark doc`，第一批建议只做这些最常用块：

- `title`
- `text`
- `bullet`
- `ordered`
- `code`
- `quote`
- `callout`
- `divider`

原因很直接：

- 官方明确支持。
- SDK 已有对应 builder。
- 这些块已经覆盖周报、纪要、总结、知识整理的主干需求。

### 3. 不要继续把“格式转换”做成黑箱

如果以后需要从 Markdown 生成飞书块，应该单独说明：

- 哪些 Markdown 语法会映射成什么块。
- 哪些语法会退化成普通文本。
- 哪些语法当前不支持。

而不是直接宣称“支持 Markdown 文件写入”，这会让用户预期过高。

## 建议的下一步

建议按下面顺序推进，而不是继续往 `append-file` 上堆启发式转换：

1. 先补一份结构化块设计文档。
2. 明确 CLI 形态，例如：
   - `chattool lark doc append-title`
   - `chattool lark doc append-list`
   - `chattool lark doc append-callout`
   - 或者统一走 `chattool lark doc append-block --type ...`
3. 用真实飞书文档做 e2e 验证，确认每种块的最小有效载荷。
4. 最后再考虑“Markdown 到飞书块”的映射层。

## 对 Skill 的影响

`skills/feishu` 里的文档和示例需要收敛到官方能力边界：

- 不再把当前实现描述成“Markdown 文档写入已经成熟”。
- 明确区分“纯文本段落追加”和“结构化块创建”。
- 所有结构化能力的说法，都应先以官方 API 文档为准，再决定是否进入 CLI。

## 临时结论

在没有补完结构化块 CLI 之前，飞书文档能力应按下面的话术描述：

- 当前稳定能力：创建文档、读取文档、查看块、追加纯文本、从文件提取段落并追加。
- 官方支持但 CLI 尚未完整暴露：标题、列表、代码块、引用块、高亮块、callout 等结构化块。
- 后续实现方向：优先补结构化块，而不是继续扩“伪 Markdown 渲染”。
