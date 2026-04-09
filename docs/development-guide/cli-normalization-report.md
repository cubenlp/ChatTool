# CLI 规范化现状报告

## 目的

这份报告用于记录当前 ChatTool 仓库内 CLI 交互规范的实际落地状态，方便后续开发时快速判断：

- 某个命令是否已经接入统一的交互 schema
- 某个命令是否仍属于旧式实现
- 当前文档是否已经和代码行为对齐
- 后续新增或改造命令时，应该参考哪一类实现

本文档是“现状盘点”，不是最终设计文档。设计原则与推荐写法见：

- `docs/design/chattool-cli-interaction-design.md`
- `docs/development-guide/index.md`

## 当前统一规范

当前推荐的 CLI 输入处理方式是：

1. Click 参数层尽量使用 `required=False`
2. 在 `src/chattool/interaction/command_schema.py` 中通过以下对象声明输入规范：
   - `CommandField`
   - `CommandSchema`
   - `CommandConstraint`
3. 在命令函数里统一调用：
   - `resolve_command_inputs()`
4. 用共享装饰器接入统一交互开关：
   - `@add_interactive_option`

统一行为约定：

- 缺参时默认自动补问
- `-i` 强制进入交互补参流程
- `-I` 禁用交互；若缺参则直接报错
- 可恢复缺参不应继续依赖 Click 的 `required=True` 或默认必填位置参数

## 已接入共享 schema 的命令

以下命令已经接入共享的 `command_schema` 机制，可作为新命令实现时的直接参考。

### DNS

- `chattool dns ddns`
- `chattool dns set`
- `chattool dns get`
- `chattool dns cert-update`

行为：

- 在交互终端里缺少关键参数时会自动补问
- `dns` 根命令可先进入命令选择页

### Client

- `chattool client cert apply`
- `chattool client cert download`
- `chattool client svg2gif`

行为：

- 缺少 domain / email / svg_path 等关键输入时自动补问
- `client cert` 的邮箱默认会优先尝试 `git config user.email`

### GitHub

- `chattool gh pr-create`
- `chattool gh pr-view`
- `chattool gh pr-check`
- `chattool gh run-view`
- `chattool gh job-logs`
- `chattool gh pr-comment`
- `chattool gh pr-merge`
- `chattool gh pr-update`

行为：

- 缺少 PR 编号、run id、job id、base/head/title/comment body 等关键参数时自动补问

### Zulip

- `chattool zulip topics`
- `chattool zulip topic`

行为：

- 缺少 `stream` / `topic` 时自动补问

### Image

- `chattool image liblib generate`
- `chattool image huggingface generate`
- `chattool image tongyi generate`
- `chattool image pollinations generate`
- `chattool image siliconflow generate`

行为：

- 各家 `generate` 在缺少 `prompt` 时自动补问
- `huggingface generate` 缺少 `output` 时也会自动补问

### Chatenv

- `chatenv save`
- `chatenv use`
- `chatenv delete`
- `chatenv set`
- `chatenv get`
- `chatenv unset`
- `chatenv test`

行为：

- 缺少 profile 名、key、`KEY=VALUE`、target 时自动补问

### Explore / Network / TPLink

- `chattool explore arxiv get`
- `chattool network ping`
- `chattool tplogin ufw add`

行为：

- 缺少 arXiv ID、network、rule spec 时自动补问

## 已统一交互策略，但尚未迁到共享 schema 的命令

以下命令已经有较成熟的 interactive policy，但当前仍主要使用较早一代的写法，例如：

- 直接在命令内部调用 `resolve_interactive_mode()`
- 直接在命令内部调用 `abort_if_missing_without_tty()`
- 手动编排 `ask_text()` / `ask_select()`

这类命令的行为通常已经接近统一规范，但风格尚未完全收口到 `CommandSchema`。

当前主要包括：

- `chattool pypi init`
- `chattool cc` 的部分交互命令
- `chattool setup workspace`
- `chattool setup frp`
- `chattool setup opencode`
- `chattool setup lark-cli`
- `chattool setup claude`
- `chattool setup codex`
- `chattool setup chrome`
- `chattool setup docker`
- `chattool setup cc-connect`

判断建议：

- 如果只是功能保持和小修，当前写法通常可接受
- 如果后续要大改输入流程，建议直接迁到 `CommandSchema`

## 当前明确例外

### `chatpypi`

当前新增了独立脚本入口：

- `chatpypi`

它的行为不是简单 alias，而是带路由规则的快捷入口：

- `chatpypi mypkg` 会自动转成 `chattool pypi init mypkg`
- `chatpypi build` 会转成 `chattool pypi build`

这属于明确例外，目的是优化高频初始化体验。后续如果引入类似快捷入口，应在设计文档里单独说明，不要隐式扩散。

### `setup alias` 的输出

`chattool setup alias` 现在在 dry-run / 更新提示中使用了带颜色的 `[info]` 和 `[dry-run]` 风格输出。这属于展示层改进，不影响共享交互 schema 本身。

## 当前文档对齐情况

### 已基本对齐

- `docs/development-guide/index.md`
- `docs/design/chattool-cli-interaction-design.md`
- `README.md`
- `docs/tools/dns/index.md`（大部分场景）

### 仍建议继续校对的点

截至本报告编写时，仍建议继续检查以下文档中是否保留旧式“必填参数”表述：

- `docs/client.md`
  - `dns set` 的 `--value`
  - `dns cert-update`
  - `client cert`
  - `network ping`
  - `gh`
  - `zulip`
  - `env/chatenv` 章节
- `docs/tools/dns/index.md`
  - `cert-update` 参数说明是否仍写成“必填”而未说明交互补问
- `docs/tools/network/index.md`
  - `network ping --network` 是否仍只描述为“必填”

这里的核心不是“字段是否重要”，而是要明确：

- 在交互终端里，这些字段缺失时会自动补问
- 只有显式 `-I` 或非交互环境时，才保持直接报错

## 后续判断建议

当你在后续开发中遇到 CLI 变更，建议按下面顺序判断。

### 情况 1：新命令

直接按共享 schema 写：

- `CommandField`
- `CommandSchema`
- `CommandConstraint`
- `resolve_command_inputs()`
- `@add_interactive_option`

### 情况 2：旧命令小修

如果只是补一个字段、调一个默认值、改一条提示文案：

- 可以暂时保持原实现
- 但如果命令本身已经有较复杂的 `missing_required` / prompt 样板，优先趁机迁到 schema

### 情况 3：旧命令重做交互流程

如果涉及：

- 新增多个关键字段
- 改变缺参逻辑
- 增加 `-i/-I`
- 重新组织 prompt 顺序

建议直接切到共享 schema，不再继续叠加旧式 helper。

## 简短结论

当前仓库的 CLI 规范主线已经比较清晰：

- 高频命令已经大面积切到共享 schema
- 新开发规范和 design 文档已经同步
- 剩余主要是“行为已较统一、风格未完全收口”的旧命令，以及少量用户文档残留

后续工作的重点，不再是重新设计规范，而是：

1. 持续把剩余旧命令迁到共享 schema
2. 持续把用户文档里的旧式“必填参数”表述改成当前真实行为
