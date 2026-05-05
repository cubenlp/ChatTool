# ChatStyle

外部 `chatstyle` 包是 ChatArch CLI 交互规范的 canonical runtime。ChatTool 内的 `chattool.chatstyle` 只保留兼容 facade，`chattool.interaction` 只保留 ChatTool 侧 adapter。业务命令只应描述字段、参数和业务行为，不应重复实现 TTY 检查、prompt backend、mask 规则或 `-i/-I` help 文案。

英文版见：[chatstyle.en.md](chatstyle.en.md)。

## 模块边界

- `chatstyle.render` / `chattool.chatstyle.output`
  - 标题、提示、Rich/click fallback 渲染，以及通用展示 helper。
- `chatstyle.tui` / `chattool.chatstyle.prompt`
  - `ask_text()`、`ask_path()`、`ask_confirm()`、`ask_select()`、`ask_checkbox()`、`ask_checkbox_with_controls()` 和 TTY 可用性检测。
- `chatstyle.tui` / `chattool.chatstyle.choice`
  - `create_choice()`、`get_separator()`、choice 归一化和 questionary 样式。
- `chatstyle.security` / `chattool.chatstyle.mask`
  - `mask_secret()`、当前敏感值展示，以及“回车保留当前值”的敏感输入行为。
- `chatstyle.render` flow helper / `chattool.chatstyle.setup`
  - setup 类阶段展示 helper：开始、阶段、成功、警告、失败、建议命令和配置优先级。
- `chatstyle.core` / `chattool.chatstyle.constants`
  - `BACK_VALUE`、checkbox indicator、`INTERACTIVE_OPTION_HELP` 等共享常量。

## Command Schema

`CommandSchema` 的 canonical 实现在外部 `chatstyle.input`。ChatTool 命令继续从 `chattool.interaction.command_schema` 导入，以便保留旧 mock 路径和 ChatTool 侧 policy adapter：

- `CommandField`
- `CommandSchema`
- `CommandConstraint`
- `resolve_command_inputs()`
- `add_interactive_option()`

对缺参后可恢复的命令，继续优先使用 `CommandSchema`。不要在 ChatTool 内复制新的 schema runtime。

## Prompt 使用规范

新的共享 prompt 行为应优先进入外部 `chatstyle`。旧的 `chattool.chatstyle.prompt` 与 `chattool.interaction.prompt` import 仍作为兼容 shim 保留。

命令参数补问优先使用 schema 驱动。只有流程本身就是页面式或向导式时，才直接调用 prompt 原语，例如分类选择、setup 模式选择或 checkbox 多选。

敏感字段应使用 password input，并以 mask 形式展示当前值。若回车应保留已有值，优先使用 `chatstyle.prompt_sensitive_value()`；旧代码可继续通过 `chattool.chatstyle.mask.prompt_sensitive_value()` 导入。

## Interactive 策略

普通命令继续使用 `chattool.interaction.command_schema` 提供的 `@add_interactive_option`。它会接入：

```text
--interactive/--no-interactive
-i/-I
```

help 文案来自外部 `chatstyle.INTERACTIVE_OPTION_HELP`，并通过 `chattool.chatstyle.constants.INTERACTIVE_OPTION_HELP` 兼容导出。

语义保持不变：

- 缺少必要值且 TTY 可用时，可以自动进入交互补问。
- `-i` 强制进入当前命令的交互流程。
- `-I` 完全禁用交互。
- 强制交互但没有 TTY 时，必须用统一的人类可读错误提示失败。

## 输出风格

可复用展示模式使用外部 `chatstyle.render`。业务模块仍可直接打印领域结果，但通用标题、提示、摘要和错误展示不应在每个命令里重复发明。

Rich 不可用时，helper 必须 fallback 到纯 Click 输出。

## Setup 风格

setup 命令应暴露可观察阶段：

- 开始
- 依赖检测
- 安装或外部操作
- 配置写入
- 验证
- 完成或失败原因

如果 setup 流程涉及 sudo，必须提供显式 `--sudo` 开关。未传 `--sudo` 时，只打印建议命令，不直接执行。建议命令展示使用外部 `chatstyle.render_suggested_commands()` 或 ChatTool facade。

setup 命令从多个来源解析值时，应一致记录和展示优先级：

```text
显式参数 > -e/--env > 工具默认配置位置 > 系统环境变量 > ChatTool .env > 默认值
```

## 迁移期兼容

旧的 `chattool.interaction` prompt、choice、render、constants 和 command schema 模块已变成指向外部 `chatstyle` 的兼容 shim。已有命令 import 和测试应继续可用。新的可复用风格能力应先加到外部 ChatStyle 项目，只有需要兼容旧入口时再通过 ChatTool shim 暴露。

## CLI 测试要求

CLI 行为继续保持 doc-first：

- 真实 CLI 测试放在 `tests/cli-tests`
- mock CLI 编排测试放在 `tests/mock-cli-tests`
- 迁移期内，patch `chattool.interaction.command_schema.ask_text` 这类旧 mock 路径仍有效

新增或修改 CLI 交互时，必须验证：

- 缺参只在允许时进入 interactive
- `-i` 与 `-I` 保持文档语义
- prompt 展示的默认值与实际执行一致
- 敏感值展示时脱敏，输入时不回显
- 非 TTY 错误可读且可操作
