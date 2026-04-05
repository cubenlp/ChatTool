# ChatTool CLI 交互统一设计

> 目标：把当前分散在 `utils/tui.py`、`setup/interactive.py`、`config/cli.py` 以及各命令内的交互判断，统一为一套 CLI 级交互框架，确保参数缺失补全、无 TTY 失败、敏感信息提示、分类选择和确认行为在整个 `chattool` 下保持一致。

## 背景

当前仓库里的 CLI 交互已经形成了可复用雏形，但还停留在“局部统一”阶段：

- `chattool setup *` 已经有相对统一的 interactive 策略。
- `chatenv init` 仍保留一套独立的配置交互流程。
- `skill install`、`gh set-token`、`setup alias` 直接调用 TUI，但没有接入同一套交互策略。
- `BACK_VALUE`、默认值展示、敏感字段保留现值等约定存在，但没有形成清晰的模块边界和统一协议。

结果是：

- 同类命令的交互触发条件不一致。
- 无 TTY 时的降级和报错不一致。
- setup 之外的 CLI 很难复用同一套行为。
- 后续新增命令时容易再次在局部实现一套新的 prompt 逻辑。

本文档定义统一方案，作为后续重构和新命令接入的基线。

## 设计目标

- 为整个 ChatTool CLI 提供一套统一的交互策略层，而不是只服务 `setup/`。
- 统一 `-i` / `-I` / 自动补全的语义。
- 统一 select、checkbox、text、password、confirm 的表现形式和按键习惯。
- 统一“当前值”“默认值”“脱敏值”的展示规则，并保证提示与最终写入遵循同一优先级。
- 让 `setup`、`chatenv`、`skill`、`gh`、未来新命令都能复用同一套模式。
- 在不破坏现有命令的前提下，支持渐进式迁移。

## 非目标

- 不追求在一阶段重写所有 CLI 命令。
- 不要求所有命令都必须先出现一个菜单页。
- 不把 CLI 交互框架设计成通用 UI 系统；目标仍然是服务当前仓库的命令行体验。
- 不在本设计中引入新的配置优先级规则；这里只统一交互和入口行为。

## 当前问题归纳

### 1. 模块边界不清

- `utils/tui.py` 同时承载渲染、选择控件、文本输入和若干兼容垫片。
- `setup/interactive.py` 只存在于 setup 命令空间，但其中的策略实际上适用于更多 CLI。
- 一些命令直接在自身模块里做 interactive 判断，导致策略层无法复用。

### 2. 交互触发条件不一致

- 有些命令“缺参才 prompt”。
- 有些命令“只要检测到已有配置就 prompt”。
- 有些命令没有 `-i/-I`，只能隐式判断是否进入 prompt。

### 3. 取消与返回协议不完整

- 代码中存在 `BACK_VALUE` 约定，但并不是所有 prompt 都真正支持“返回上一级”。
- 调用方是否应该把取消视为 `Abort`、返回上级还是静默返回，目前不统一。

### 4. 命令间提示模式不统一

- 敏感值“回车保留当前值”的模式有些命令有，有些命令没有。
- 多选页面的 select-all 和键位行为仅在部分命令上可见。
- profile 选择、覆盖确认、目标平台选择等高频模式仍在各命令重复实现。

## 目标目录结构

建议把交互能力提升到 CLI 级目录，统一放在：

```text
src/chattool/cli/interaction/
  __init__.py
  types.py
  policy.py
  choice.py
  render.py
  prompt.py
  patterns.py
```

各文件职责如下。

### `types.py`

- 定义交互层共享常量和数据结构。
- 例如：
  - `BACK_VALUE`
  - `PromptDecision`
  - `PromptContext`
  - `OverwriteAction`

目标是把“字符串协议”尽量提升为类型化对象，减少各命令自行拼装状态。

### `policy.py`

- 负责是否允许交互、是否需要交互、何时应失败。
- 统一承载：
  - `is_interactive_available`
  - `normalize_interactive`
  - `resolve_interactive_mode`
  - `abort_if_force_without_tty`
  - `abort_if_missing_without_tty`

这部分是整个设计的行为中枢。

### `choice.py`

- 负责统一选择项表示与标准化。
- 统一承载：
  - `create_choice`
  - `get_separator`
  - `_normalize_choice`

目标是让所有 select / checkbox 都共享相同 choice 结构，而不是每个命令自己拼格式。

### `render.py`

- 负责 heading、note、fallback 文本渲染。
- 统一承载：
  - `_get_console`
  - `_render_heading`
  - `_render_note`

目标是把 Rich 相关展示能力和具体 prompt 控件解耦。

### `prompt.py`

- 负责基础 prompt 原语。
- 统一承载：
  - `ask_select`
  - `ask_checkbox`
  - `ask_checkbox_with_controls`
  - `ask_text`
  - `ask_path`
  - `ask_confirm`

这些函数只负责“如何问”，不负责业务规则。

### `patterns.py`

- 负责高频交互模式的收敛。
- 建议提供：
  - `prompt_secret_keep_current`
  - `prompt_text_keep_default`
  - `prompt_platform_if_missing`
  - `prompt_single_config_type_if_missing`
  - `prompt_overwrite_action`
  - `prompt_profile_name_if_missing`

目标是减少命令层重复写同一类“先判断现值，再展示默认值，再做脱敏，再处理空输入”的代码。

## 对外 API 设计

对命令实现层，应该暴露两层能力。

### 第一层：基础 prompt API

适用于简单命令，直接调用即可：

- `ask_select`
- `ask_checkbox_with_controls`
- `ask_text`
- `ask_confirm`
- `resolve_interactive_mode`

### 第二层：模式化 helper API

适用于高频重复逻辑：

- 读取当前脱敏值并支持“回车保留”
- 缺少 profile/type 时自动进入单选
- 覆盖现有文件或目录时统一确认
- 多选“全部技能 / 全部别名 / 全部 provider”时统一指令文案

命令层原则上只拼业务上下文，不自己重复定义通用交互套路。

## 统一 CLI 行为约定

### 1. interactive 三态规则

所有适合交互补参的命令，统一采用：

- `-i`：强制 interactive
- `-I`：完全禁止 interactive
- 默认：仅在“缺少必要信息”或“已有状态需要确认”时自动进入 interactive

这条规则不只适用于 `setup`，还应扩展到：

- `chatenv init`
- `skill install`
- `gh set-token`
- 未来任何会进行补参或确认的 CLI

### 2. 无 TTY 时的统一行为

- 显式 `-i` 但无 TTY：直接报错并给 usage
- 默认模式下缺少必要参数且无 TTY：直接报错并给可操作信息
- 默认模式下参数齐全且无需确认：正常继续
- 非关键确认项在无 TTY 下不得悄悄进入交互；必须走显式参数或采用明确安全默认值

### 3. prompt 展示规则

- 敏感值只能显示脱敏结果
- 若允许“回车保留当前值”，文案必须显式说明
- 展示给用户的 `current` / `default` 必须与最终实际写入遵循同一优先级
- select / checkbox 尽量保留统一键位：
  - 上下箭头或 `j/k`
  - `<space>` 切换
  - `<enter>` 确认
  - 多选支持 `a` 切换全选

### 4. 取消与返回规则

统一区分三种结果：

- `Abort`：用户取消整个命令
- `Back`：仅返回上一级页面
- `Empty`：用户输入空值，按字段语义处理

建议后续逐步把 `BACK_VALUE` 从裸字符串协议迁移为更清晰的类型或枚举；在迁移完成前，旧协议仍保留兼容层。

## 命令层接入规则

### 1. setup 命令

`setup/*` 是第一批完整接入对象。

- 保持当前已有的 `resolve_interactive_mode` 模式
- 把实现从 `setup/interactive.py` 迁移到 CLI 级目录
- 保持 `setup codex`、`setup lark-cli`、`setup opencode`、`setup workspace` 的现有语义不变

### 2. chatenv

`chatenv` 需要从“自带一套交互流程”改为“复用统一交互框架”。

目标：

- `chatenv init` 接入统一的 interactive policy
- provider 选择、category 选择、profile type 选择复用统一 select / patterns
- 敏感字段输入统一走同一套 secret prompt helper

### 3. skill

`skill install` 已经部分复用多选控件，但还没有接入完整策略层。

目标：

- 缺少 `--platform` 时走统一平台选择
- 缺少 skill name 时走统一多选
- 覆盖确认走统一 overwrite action
- 后续补上 `-i/-I` 语义

### 4. gh / 零散工具命令

例如 `gh set-token` 目前只在缺 token 且有 TTY 时补问一次。

目标：

- 这类命令也统一接入 policy 和 secret prompt helper
- 不再在各模块里单独写一套 token prompt 逻辑

## 兼容迁移策略

为避免大规模改动一次性破坏现有命令，迁移采用两层兼容。

### 兼容层一：保留旧 import 路径

以下文件先改为薄 re-export：

- `src/chattool/utils/tui.py`
- `src/chattool/setup/interactive.py`

这样可以先搬实现，再逐步改调用方，不要求一次性替换所有 import。

### 兼容层二：保留旧协议

- 现阶段继续保留 `BACK_VALUE`
- 继续允许老调用方基于 `BACK_VALUE` 判断
- 新 helper 优先返回更明确的状态对象，但在边界层转换回旧协议，直到全部调用方迁完

## 推荐实施顺序

### 阶段 1：纯搬迁，不改行为

- 新建 `src/chattool/cli/interaction/`
- 把现有实现按职责拆分
- `utils/tui.py`、`setup/interactive.py` 改成兼容导出
- 目标：现有测试不变，行为不变

### 阶段 2：setup 全量切新目录

- `setup/*` 的 import 全部切到 `cli/interaction`
- 保持行为不变
- 修掉历史命名错位，例如把实际承载 API key 的参数名从误导性命名中清理出来

### 阶段 3：chatenv / skill / gh 收敛

- `chatenv init` 接入统一 policy 和 patterns
- `skill install`、`gh set-token` 接入统一策略
- 把各自重复的 prompt 逻辑删掉

### 阶段 4：统一交互参数暴露

- 对适合交互补参的非 setup 命令逐步补齐 `-i/-I`
- 文档与帮助信息统一说明默认行为

## 测试要求

### 单元测试

新增测试重点：

- `policy.py`
  - 默认 / `-i` / `-I` 三态解析
  - 无 TTY 时的错误分支
- `choice.py`
  - choice 标准化
  - separator 处理
- `patterns.py`
  - secret keep-current
  - overwrite action
  - 缺省选择逻辑

### Mock CLI Tests

重点验证：

- 缺少参数时是否自动进入交互
- `-I` 是否阻止交互
- `-i` 在无 TTY 时是否明确失败
- prompt 展示出的 current/default 是否与实际落盘一致
- 多选控件是否复用统一行为

### 真实 CLI Tests

重点验证：

- setup 和 chatenv 的真实交互链路仍可用
- 从显式参数、配置对象、typed env 和已有工具配置合并出的默认值是否一致

## 文档要求

迁移过程中，以下文档需要同步维护：

- `docs/development-guide/index.md`
- `docs/env/*.md` 中涉及 interactive 的命令页
- `README.md` 中涉及主要 CLI 行为的说明

文档中关于交互行为的描述，统一使用本设计中的术语：

- 强制 interactive
- 禁止 interactive
- 自动补参
- 当前值
- 默认值
- 脱敏值

避免各文档分别使用不同说法。

## 成功标准

完成统一后，应满足以下结果：

- 新命令不再需要自行发明 interactive 判断逻辑。
- setup、env、skill、gh 的关键交互行为一致。
- 无 TTY、缺参、取消、确认等边界行为有统一定义。
- TUI 代码不再散落在 `setup/` 和各命令文件中。
- 交互变更可以通过共享测试覆盖，而不是每个命令单独兜底。
