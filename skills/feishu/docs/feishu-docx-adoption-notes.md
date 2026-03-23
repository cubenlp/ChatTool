# feishu-docx 摘取建议

这份文档记录对 `feishu-docx` 的初步拆解结果，目标不是直接整包引入，而是明确哪些模块值得摘取到 ChatTool，哪些不值得带进来。

## 来源

- 项目：`https://github.com/leemysw/feishu-docx`
- 发布包：`feishu_docx-0.2.2-py3-none-any.whl`

本次没有直接把整仓库并入当前项目，而是通过 wheel 解包查看实际发布内容，避免被仓库里无关文件干扰。

## 先说结论

不建议直接把 `feishu-docx` 作为 ChatTool 的硬依赖。

原因：

- 它要求 `Python >=3.11`，而 ChatTool 当前是 `>=3.9`。
- 它的范围太大，不只是 docx 写入，还包括 OAuth、Drive、TUI、Wiki、Bitable、WeChat 导入等。
- 你当前真正需要的是“Markdown / 中间 JSON / 飞书 Block”这一条写入链，而不是整套新 CLI。

更合理的方式是：

- 保持 ChatTool 自己的 CLI、配置、skill 结构不变。
- 摘取一小部分实现思路和局部代码。
- 先在 `src/chattool/tools/lark/` 下重构自己的结构化文档链路。

## 包内结构

wheel 里和当前需求直接相关的目录主要有：

- `feishu_docx/core/converters/md_to_blocks.py`
- `feishu_docx/core/writer.py`
- `feishu_docx/core/sdk/docx.py`
- `feishu_docx/schema/models.py`

其他模块大多偏外围或超出当前目标：

- `auth/`：OAuth / tenant token
- `cli/`：完整 CLI 体系
- `tui/`：Textual UI
- `core/exporter.py`：导出链路
- `core/parsers/*`：文档导出解析
- `core/wechat_importer.py`：微信公众号导入
- `core/sdk/drive.py`、`wiki.py`、`sheet.py`、`bitable.py`：超出当前最小目标

## 值得摘的部分

### 1. `core/converters/md_to_blocks.py`

这是当前最值得参考的一块。

它已经做了：

- 使用 `mistune` 解析 Markdown
- 将 Markdown token 转成飞书 block dict
- 支持标题、段落、列表、代码块、引用、分割线
- 还覆盖了图片、表格、数学公式

对 ChatTool 最有价值的不是“整文件照搬”，而是这些设计点：

- Markdown 先转结构块，而不是先压成纯文本
- block type 常量清晰
- heading / bullet / ordered / code / quote / divider 的映射明确
- 文件导入和结构块生成是独立的

建议摘取方式：

- 不直接复制整个文件
- 参考其 `MarkdownToBlocks` 的整体分层
- 在 ChatTool 里重写成更小的第一版，只保留：
  - heading
  - paragraph
  - bullet
  - ordered
  - code
  - quote
  - divider
  - callout

### 2. `core/sdk/docx.py`

这个模块也值得参考，但只建议摘取最小片段。

它做得比较好的地方：

- 对飞书创建块请求做了统一 normalize
- `create_blocks()` 做了每批 50 个子块的分片
- 单独封装了 `get_document_info`、`get_block_list`、`get_block_children`

这些都是 ChatTool 当前文档 CLI 可以直接借鉴的。

建议摘取方式：

- 不引入整套 `FeishuSDK`
- 只把 docx 相关的 payload normalize、分页获取、批量创建这三种思路迁到 `chattool.tools.lark`
- 继续沿用 ChatTool 当前 `LarkBot` 和配置体系

### 3. `schema/models.py`

这个文件的价值比较直接：提供了一份相对完整的 BlockType 枚举。

这对 ChatTool 现在很有用，因为你已经开始进入结构化块设计阶段。

建议摘取方式：

- 可以直接参考它的枚举定义
- 但不要把整个 schema 系统一起带进来
- 在 ChatTool 里保留一份更小的常用块枚举就够了

## 不建议摘的部分

### 1. `core/writer.py`

这个文件虽然和“写入”最相关，但现在不建议直接摘。

原因：

- 它已经带上了自己的 `FeishuSDK`
- 里面混了图片补写、表格拆块、递归创建、控制台输出等很多策略
- 对 ChatTool 当前目标来说太重

可以参考其两点：

- 递归创建嵌套块
- 表格内容分阶段写入

但不建议直接搬进来。

### 2. 整个 `cli/`

不建议摘。

原因：

- ChatTool 已经有自己的 CLI 入口和参数规范
- 直接引入会和 `chattool lark` 的风格冲突
- 还会把 `typer` 系命令组织引入现有 `click` 体系，增加复杂度

### 3. `tui/`、`auth/`、`wechat_importer.py`

当前都不值得碰。

这些不是你现在的主矛盾，会把改造范围带偏。

## 对 ChatTool 的最小重构建议

不要沿着“`append-file` 继续扩启发式转换”走下去。

建议在 `src/chattool/tools/lark/` 下拆成三块：

### A. `docx_blocks.py`

职责：

- 定义常用 block type
- 提供 block builder
- 负责 `normalized_json -> Feishu block payload`

### B. `markdown_blocks.py`

职责：

- `Markdown -> normalized_json`
- 或直接 `Markdown -> block dict`

第一版先只支持：

- heading
- paragraph
- bullet
- ordered
- code
- quote
- divider
- callout

### C. `cli.py`

补三个命令，而不是继续把所有能力塞进 `append-file`：

- `chattool lark doc parse-md file.md`
- `chattool lark doc append-json <document_id> blocks.json`
- `chattool lark doc import-md <document_id> file.md`

## 最适合“摘过来”的清单

如果真的要动手摘，建议优先看这几个文件：

- `/tmp/feishu-docx-wheel/feishu_docx/core/converters/md_to_blocks.py`
- `/tmp/feishu-docx-wheel/feishu_docx/core/sdk/docx.py`
- `/tmp/feishu-docx-wheel/feishu_docx/schema/models.py`

不建议直接摘的：

- `/tmp/feishu-docx-wheel/feishu_docx/core/writer.py`
- `/tmp/feishu-docx-wheel/feishu_docx/cli/*`
- `/tmp/feishu-docx-wheel/feishu_docx/tui/*`

## 当前判断

`feishu-docx` 很适合作为参考实现，也适合局部摘取设计和少量代码。

但它不适合在当前阶段直接作为 ChatTool 的硬依赖，更不适合直接把整套 writer/cli 搬进来。最稳的路线仍然是：

- 借鉴它的 `md_to_blocks` 和 `docx` API 组织方式
- 在 ChatTool 里保留自己的 CLI、配置和 skill 体系
- 逐步把飞书文档能力收敛成结构化块链路
