# ChatTool Feishu 设计

> 目标：把飞书能力统一整理成一套可持续演进的 ChatTool 开发结构。这个文档不是现状调研，而是后续开发时应对齐的目标形态。

## 设计目标

- 用 `chattool lark` 作为飞书能力的统一 CLI 主入口。
- 优先把高频、稳定、可复用的飞书操作沉淀成 CLI，而不是继续堆一次性脚本或零散 skill。
- 用 `skills/feishu/` 作为飞书主 skill，负责路由、能力地图和入口说明。
- 将复杂专题能力写成 `skills/feishu/` 根目录下的专题 `.md`，而不是拆 sibling skill 目录。
- 将官方 API、格式约束、字段结构等内容下沉为同目录 reference 文档，而不是直接塞进主 skill。
- `SKILL.md` 只做索引；安装时会整目录拷贝，因此主 skill 包内可以直接放专题 `.md`、reference 与样例说明。

## 非目标

- 不在主 skill 中保留超长操作手册。
- 不把 OpenAPI 原文搬运进 CLI 设计文档。
- 不把所有飞书域能力一次性塞进 `chattool lark` 顶层命令。
- 不允许飞书开发继续分散到多个没有边界的入口中。

## 一阶段目标形态

飞书能力最终按三层组织：

1. **CLI 主入口**
   - `chattool lark`
2. **飞书主 skill**
   - `skills/feishu/`
3. **专题文档与 reference**
   - 文档、消息、IM read、bitable、calendar、task、排障、字段规则、格式边界等

## CLI 主入口设计

### 总原则

- 飞书相关普通操作默认优先映射到 `chattool lark`
- 子命令应面向“用户动作”，不是面向 OpenAPI 资源名
- 高复用能力优先做命令，不优先暴露内部 SDK 细节
- CLI 参数承载业务输入，不新增临时环境变量传消息内容、接收者、文件路径等一次性参数

### 顶层命令边界

`chattool lark` 一阶段应稳定承载这些能力：

```text
chattool lark info
chattool lark scopes
chattool lark send
chattool lark upload
chattool lark reply
chattool lark notify-doc
chattool lark listen
chattool lark chat
chattool lark doc ...
```

### 顶层命令职责

#### `chattool lark info`

- 用途：验证飞书凭证、查看机器人是否激活
- 定位：接入验证入口

#### `chattool lark scopes`

- 用途：查看应用权限范围
- 定位：排查消息/文档能力前的权限入口

#### `chattool lark send`

- 用途：统一消息发送入口
- 支持：
  - 文本
  - 图片
  - 文件
  - 卡片
  - 富文本
- 要求：
  - 默认接收者回退到 `FEISHU_DEFAULT_RECEIVER_ID`
  - 业务输入走 CLI 参数

#### `chattool lark upload`

- 用途：单独上传图片/文件，返回资源 key
- 定位：卡片、富文本、后续结构化消息能力的前置工具

#### `chattool lark reply`

- 用途：引用回复已有消息
- 定位：消息链路中的高频补充能力

#### `chattool lark notify-doc`

- 用途：创建文档、写正文、发送链接
- 定位：面向“生成结果沉淀到文档并通知用户”的高频工作流
- 要求：
  - 支持 `--append-file`
  - 支持 `--open`
  - 支持默认接收者

#### `chattool lark listen`

- 用途：调试长连接事件接收
- 定位：开发与排障入口

#### `chattool lark chat`

- 用途：在本地终端验证会话链路
- 定位：开发与提示词调试入口

## `doc` 子命令设计

文档能力统一收敛到 `chattool lark doc` 分组，而不是继续散落成多个平级顶层命令。

一阶段稳定命令面如下：

```text
chattool lark doc create
chattool lark doc get
chattool lark doc raw
chattool lark doc blocks
chattool lark doc append-text
chattool lark doc append-file
chattool lark doc parse-md
chattool lark doc append-json
```

### `doc` 分组职责

#### `create`

- 创建飞书云文档

#### `get`

- 获取文档元信息

#### `raw`

- 获取文档纯文本内容

#### `blocks`

- 查看文档块结构

#### `append-text`

- 追加纯文本段落

#### `append-file`

- 从本地 `txt/md` 文件提取正文后追加
- 该命令走稳定路线，优先保证写入成功率

#### `parse-md`

- 将 Markdown 转换为 docx block JSON
- 定位：结构化文档能力的开发与调试工具

#### `append-json`

- 将 block JSON 追加进文档
- 定位：面向更原生的 docx 结构化写入

## 文档处理的双轨模型

飞书文档相关开发，统一按双轨模型推进：

### 轨道 A：稳定正文轨

- 入口：
  - `doc append-text`
  - `doc append-file`
  - `notify-doc`
- 特点：
  - 适合正文沉淀
  - 优先保证写入成功率
  - 允许 Markdown 降级为普通段落

### 轨道 B：结构化 docx 轨

- 入口：
  - `doc parse-md`
  - `doc append-json`
- 特点：
  - 适合标题、列表、代码块、引用块等结构化内容
  - 应以官方 docx block 能力为准
  - 后续结构化增强优先在这条线上推进

后续新增 doc 能力时，必须先判断属于哪条轨道，避免把“稳定写正文”和“追求结构化表达”混成一套逻辑。

## 代码落点设计

飞书 CLI 相关实现统一放在：

```text
src/chattool/tools/lark/
```

目录职责如下：

- `__init__.py`
  - 对外暴露稳定 API
- `cli.py`
  - 只处理 CLI 参数、交互、输出
- `bot.py`
  - 飞书机器人与文档 API 封装
- `session.py`
  - 本地 chat 会话逻辑
- `context.py`
  - 消息上下文对象
- `docx_blocks.py`
  - docx block 级别的数据结构和写入辅助
- `markdown_blocks.py`
  - Markdown 到 docx block 的解析
- `elements.py`
  - 卡片或消息元素封装

### 开发要求

- CLI 层不直接堆业务判断，复杂逻辑下沉到 `bot.py`、`markdown_blocks.py`、`docx_blocks.py`
- 新增结构化文档能力时，优先扩 `docx_blocks.py` / `markdown_blocks.py`
- 新增普通发送/上传/查询能力时，优先扩 `bot.py`
- 不在 `cli.py` 内部堆大量协议细节

## Skill 组织设计

### 主 skill：`skills/feishu/`

主 skill 只承担四件事：

1. 说明飞书能力总入口是 `chattool lark`
2. 给出能力地图
3. 给出路由规则
4. 指向同目录下的专题文档和 reference

主 skill 不再承担：

- 长篇 CLI 教程
- 旧的 create/fetch/update-doc 分裂入口
- 大段 API 原文搬运

### 主 skill 包形态

```text
skills/feishu/
├── SKILL.md
├── SKILL.zh.md
├── setup-and-routing.md
├── messaging.md
├── documents.md
├── bitable.md
├── calendar.md
├── im-read.md
├── task.md
├── troubleshoot.md
├── channel-rules.md
├── api-reference.md
├── official-docx-capabilities.md
├── feishu-docx-adoption-notes.md
├── bitable-field-properties.md
├── bitable-record-values.md
├── bitable-examples.md
└── lark-markdown-syntax.md
```

说明：

- `SKILL.md` / `SKILL.zh.md` 只保留入口、能力地图、路由规则。
- 真正的工作材料下沉到 `skills/feishu/` 根目录的专题 `.md`。
- 文档读写类旧 skill 直接并回主 skill，不再单独维护。
- reference 资料也留在同一个主 skill 目录下，不再拆 sibling skill 目录。
- 不把全量 API 参数说明或巨大字段格式表塞进 `SKILL.md`。

### 主 skill 目录结构

```text
skills/feishu/
├── SKILL.md
├── SKILL.zh.md
├── setup-and-routing.md
├── messaging.md
├── documents.md
├── bitable.md
├── calendar.md
├── im-read.md
├── task.md
├── troubleshoot.md
├── channel-rules.md
├── api-reference.md
├── official-docx-capabilities.md
└── feishu-docx-adoption-notes.md
```

### 单目录原则

- 飞书只保留一个 skill 目录：`skills/feishu/`
- 其他飞书专题不再拆成 `feishu-*` sibling skill 目录
- 主入口负责路由，专题说明用根目录平铺 `.md`
- reference 资料也跟随主 skill 一起分发

## Reference 设计

reference 的定位不是给用户直接执行，而是给模型和开发者理解边界。

适合放到同一目录下的 reference 内容包括：

- 官方 docx 块能力矩阵
- bitable 字段 property 规则
- bitable 记录值格式
- adoption notes
- 特殊格式约束

不应把 reference 当作新的独立 skill 使用。

## 当前已支持与后续补齐的边界

### 已经应视为主线的能力

- 机器人验证
- 权限查看
- 消息发送
- 资源上传
- 引用回复
- 文档创建
- 文档读取
- 文档正文追加
- Markdown 转 block JSON
- block JSON 写入
- 本地 chat 调试
- WebSocket 监听调试

### 已有能力但尚未统一进 `chattool lark` 主线

- Bitable
- Calendar
- Task
- IM 历史消息读取 / 线程 / 搜索 / 下载

这些能力应先定成 `chattool lark <topic> ...` 的目标命令面和 `cli-tests/*.md`，再逐步补进 CLI 主线。

## 开发原则

后续飞书开发统一遵循以下规则：

1. 新飞书能力优先判断是否应该进入 `chattool lark`
2. 如果一阶段还没实现 CLI，先写目标命令和 `cli-tests/*.md`
3. 主 skill 只做路由，不做长教程
4. CLI 是最终交付面，reference 只是辅助理解材料
5. 文档写入能力按“稳定正文轨 / 结构化 docx 轨”双轨推进
6. 飞书开发不得继续分散到多个无边界入口

## 结论

飞书能力的目标形态不是“再多写几份说明”，而是形成一套清晰结构：

- `chattool lark` 负责高频稳定 CLI
- `skills/feishu/` 负责统一路由
- 同目录专题 `.md` 负责专题能力与 reference
- reference 负责官方边界与格式知识

后续所有飞书相关开发，都应围绕这个结构推进，而不是继续累积零散脚本、长篇 skill 手册或无边界文档。
