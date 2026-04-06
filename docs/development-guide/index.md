# Development Guide

本文档用于统一 ChatTool 的板块用途与开发规范，确保在快速迭代下依然保持结构稳定、行为一致。

## 目标

- 明确各板块职责边界，避免逻辑在入口层与实现层之间漂移。
- 统一 CLI 交互行为与配置读取规范。
- 将文档结构直接映射代码结构，降低协作和维护成本。

## 板块用途

### 1) `llm/`

- 负责模型路由、基础对话接口与流式接口。
- 对外提供稳定 Python API，供 `tools/serve/client` 复用。
- 不承载具体业务 Tool 逻辑。

### 2) `config/`（env 管理）

- 统一管理环境变量与默认值加载。
- 统一解析顺序：默认是 `CLI / 调用方显式参数 > tool config file > environment variable > ChatTool .env > default value`。
- 对支持 `-e/--env` 这类显式 env 覆盖源的命令，统一解析顺序是 `CLI / 调用方显式参数 > -e/显式 env > tool config file > environment variable > ChatTool .env > default value`。
- `ChatTool .env` 指 `envs/<Config>/.env`；profile 固定放在 `envs/<Config>/<profile>.env`，不是当前工作目录下的 `.env`。
- 以模块化配置对象组织，支持按功能扩展。
- 凡是已经注册到 `src/chattool/config/` 的配置项，业务代码与 CLI 默认值读取都应优先走配置对象（如 `OpenAIConfig.OPENAI_API_KEY.value`），不能只直接读取 `os.environ`。
- 这样才能保证 `chattool ...` 与独立入口（如 `chatskill`）都能正确读取 `chatenv` 管理的 `.env` 默认值。
- `chatenv cat -t <type>` 展示的也应是这套“生效值”，而不是只机械打印 `.env` 文件里已有的行；开发时不要把它理解成纯文件查看器。
- 运行时通过 `BaseEnvConfig.set()` 做的是当前进程内覆盖，不会自动回写 `.env`，也不改变系统环境变量；开发时不要把它误当成配置持久化机制。
- 新命令若需要“临时切换一份配置执行”，优先复用这套 `-e/--env` 机制，不要再单独发明新的环境变量或优先级。

### 3) `tools/`（核心能力）

- 每个工具目录负责该能力的完整实现。
- 同一工具应优先收敛三类接入：
  - Python API
  - CLI 命令
  - MCP 工具定义（如需要）
- CLI 交互体验通过通用策略层与 `src/chattool/interaction/` 统一增强。

### 4) `skills/`

- 面向 Agent 的能力出口。
- 将工具能力按场景组织为可复用技能，不重复实现底层逻辑。
- 每个 skill 至少维护 `SKILL.md`，仓库内如提供中文版本则同步维护 `SKILL.zh.md`。
- ChatTool 仓库内的 skill frontmatter 至少维护 `name`、`description`；`version` 如有需要可作为可选元信息维护。

### 5) `setup/`

- 负责环境安装与配置初始化。
- 关键阶段必须可观测：开始、依赖检测、安装执行、配置写入、失败原因。
- 涉及 sudo 的操作默认输出可审阅指令，保持安全可回溯。
- 当 setup 命令需要同时合并显式参数、`-e`、已有工具配置和 ChatTool 配置对象时，已有工具配置优先于系统环境变量与 typed `.env`，避免已有工具配置被当前 shell 默认值意外覆盖。
- 交互页面中展示的 `current` / `default` 必须与最终实际写入遵循同一优先级，不能显示一套、落盘另一套。

### 6) `docker/`

- 维护 docker compose 模板与 `.env` 生成逻辑。
- 对外提供统一配置入口，避免模板与代码双轨漂移。

### 7) `serve/`

- 承载远程服务能力，适用于算力不足或密钥敏感场景。
- 与 `client/` 形成清晰 server-client 职责拆分。

### 8) `client/`

- 统一 `chattool` 可执行入口。
- 负责本地工具调用与远程服务调用编排。
- 只做接入与编排，不承载核心业务实现。

### 9) `mcp/`

- 负责 MCP 服务入口与工具注册编排。
- 工具实现应下放到 `tools/*/mcp.py`，避免协议层与业务层耦合。

## CLI 开发原则

- **命令优先，交互兜底**：优先保证命令行参数可以完整表达意图；在必要参数缺失时，再进入 interactive 补全。
- **默认路径安全**：默认值应指向更安全、更可回退的路径，避免用户一次输入就触发高风险操作。
- **渐进式披露**：复杂命令按当前任务上下文逐步收集信息，不把所有问题一次性抛给用户。
- **统一体验**：相似命令共享相似的参数名、交互方式、提示文案和输出结构，避免每个子命令各自发明一套风格。
- **自动化兼容**：所有 interactive 能力都必须允许通过显式参数和 `-I` 关闭，保证脚本和 CI 可稳定运行。
- **核心逻辑下沉**：CLI 负责接入、参数解析和展示，核心逻辑应沉到 `tools/`、`config/` 或其他实现层，便于测试和复用。
- **可读输出优先**：输出要能让用户快速判断“执行了什么、结果是什么、下一步该做什么”，错误信息要可操作。
- **启动成本可控**：遵循 lazy import，避免为少量命令把整个依赖树都在 CLI 启动时拉起。

## CLI 开发规范

- 必要参数不完整时，自动触发 interactive。
- `-i` 强制 interactive，`-I` 强制非 interactive；参数不全时抛错。
- 参数提示读取默认值并显示脱敏内容（密钥必须 mask）。
- 所有新的 CLI 交互统一走 `src/chattool/interaction/`。
- 进入 interactive 后，补全当前任务相关的关键参数。
- prompt 默认值必须与实际执行一致。
- `-i` 进入当前命令交互流程，`-I` 完全禁止交互。
- 贯彻最小 import，避免 CLI 启动性能退化。

### 交互式页面风格

- ChatTool 的重点不是“必须先出现一个 select 页面”，而是整个 interactive 过程的样式、节奏和提示方式要统一。
- 入口可以是分类选择，也可以是直接逐项提问，取决于命令本身的复杂度。
- 当配置项较多、板块较多或用户目标可能分流时，优先采用“分类选择 -> 逐步补全”的交互方式。
- 典型风格参考 `chatenv init`：

```text
Starting interactive configuration...
Select a category to configure:
> Model
  DNS
  Image
  Other
```

- 对于目标非常明确、输入项很少的命令，可以直接进入逐项提问，例如 `chattool setup opencode`：

```text
INFO: Start opencode setup
? base_url https://api.openai.com/v1
? api_key
```

- 这种交互方式适用于：
  - 环境初始化
  - 安装向导
  - 多能力工具入口
  - 需要按类别拆分配置项的命令
- 不推荐在复杂命令里一开始就连续抛出大量无分组问题，这会增加理解成本，也不利于后续扩展。
- 交互式选择页应尽量复用统一的 TUI 能力与按键习惯，保持上下选择、回车确认、默认值提示、敏感信息脱敏等体验一致。
- 逐项提问的命令也应保持同样的风格约束：先输出开始信息，问题文案简短明确，默认值可见，敏感字段不回显。
- 带默认值的向导式命令，默认值也应在交互 prompt 中可见。
- 布尔确认、密码输入、仓库选择等交互保持同一套 TUI 风格。
- 如果命令最终会落到多个子板块，入口页文案应直接反映板块名，而不是使用模糊动作词，避免用户进入错误流程。

## 文档组织

- `docs/index.md`：架构总览与快速入口。
- `docs/env/`：配置与环境管理规范。
- `docs/tools/`：工具使用与能力说明。
- `docs/development-guide/`：板块用途、边界规则、开发规范。
- `docs/blog/`：实践文章与经验沉淀。

## 测试与文档

- **CLI 测试文档先行**：ChatTool 仓库内的新功能、重构和 Bugfix 如涉及 CLI 行为，必须先补对应测试线下的 `.md`。
- **双轨测试面**：
  - `cli-tests/*.md` / `cli-tests/*.py`：真实 CLI 链路与真实环境验收。
  - `mock-cli-tests/*.md` / `mock-cli-tests/*.py`：基于 mock 的 CLI 编排、参数流向、输出格式与懒加载验证。
- **真实执行测试的落点**：`cli-tests/*.py` 只作为对应 `.md` 的真实 CLI 执行实现，真实链路测试应标记为 `@pytest.mark.e2e`。
- **Mock 收纳规则**：所有使用 `mock`、`patch`、`monkeypatch`、fake client、fake API 的 CLI 测试，都必须收纳到 `mock-cli-tests/`。
- **GitHub 自动测试范围有限**：当前 `.github/workflows/ci.yml` 只跑 stable smoke tests，不包含 `lark` / `dns` 等第三方链路与大多数 `@pytest.mark.e2e`；不要把“GitHub CI 通过”误当成这些能力已验收。
- **`tests/` 的定位**：仓库根下 `tests/` 视为弃用区，只保留历史参考，不再作为新开发的默认测试落点，也不再作为交付要求。
- **禁止无文档测试实现**：没有对应 `.md` 的 CLI 测试实现不应新增。
- 对第三方集成，尤其是 Feishu，这类 `@pytest.mark.e2e` 测试必须从默认 `chatenv` / 配置对象读取生效值；如果改用 mock，只能放到 `mock-cli-tests/`。
- 如果测试依赖接收者、群聊或其他运行时参数，也应通过配置项暴露，例如 `FEISHU_DEFAULT_RECEIVER_ID`、`FEISHU_DEFAULT_CHAT_ID`，并在对应 `.md` 中写清配置要求与回滚方式。
- Feishu 相关测试设计应统一落在 `cli-tests/lark/<topic>/`；`skills/feishu/` 现在只保留紧凑入口文档，不再要求和 skill 子目录一一对齐。
- Feishu 的真实执行测试只能以这些 `cli-tests/lark/<topic>/*.md` 为准；`tests/tools/lark/` 中的历史文件不再作为主规范依据。
- Feishu 真实测试文档至少显式列出这些配置项：`FEISHU_APP_ID`、`FEISHU_APP_SECRET`、`FEISHU_DEFAULT_RECEIVER_ID`、`FEISHU_DEFAULT_CHAT_ID`。
- Feishu 测试文档必须写明回滚策略，例如删除测试消息、删除测试文档，或说明为何保留测试痕迹。
- **文档更新**：功能变更必须同步更新 `docs/` 下的文档和 `README.md`。
- **变更记录**：每次功能或修复更新必须同步更新 `CHANGELOG.md`。
- **发版记录**：每次正式发版完成后，必须先确保目标版本已在 PR/MR 阶段写入 `src/chattool/__init__.py` 与对应 `CHANGELOG.md`，再从已合并主线推送标准 tag `vX.Y.Z` 触发发布；若 PyPI 已存在该版本，必须先走新的版本 bump 变更，不能复用同版本 tag，并在仓库根目录 `release.log` 追加一条记录（时间、版本、tag、commit、执行者、摘要）。

### CLI 测试文档驱动机制（`cli-tests` / `mock-cli-tests`）

- `cli-tests` 与 `mock-cli-tests` 都采用 **doc-first**：
  - 先写 `.md`（测试目标、输入、执行顺序、预期）。
  - 文档评审通过后再实现对应 `.py`。
- `cli-tests/` 只维护真实 CLI 测试；`mock-cli-tests/` 只维护 mock CLI 测试；`tests/` 中的历史文件不再作为新样例、新要求或评审依据。
- 命名规范（与 CLI 命令保持一致）：
  - 至少一个基础文件：`test_<cli>_<command>_basic.py`
  - 按主题扩展：`test_<cli>_<command>_<topic>.py`
  - 对应文档文件同名后缀 `.md`。
- 目录建议：
  - 默认在命令目录下平铺；当某个 CLI 下面已经形成稳定专题时，可引入一层 topic 目录保持与 skill / CLI 结构一致。
  - 例如：`cli-tests/dns/test_chattool_dns_basic.md`
  - 例如：`mock-cli-tests/gh/test_chattool_gh_basic.md`
- 文档结构建议：
  - 每个 case 优先保留“初始环境准备 / 相关文件 / 预期过程和结果 / 参考执行脚本（伪代码）”结构。
  - 根据需要，可在 case 开头写必要的文字说明。
  - `预期过程和结果` 应按人类可理解顺序编写，把“执行了什么”和“紧接着预期什么”写在同一步里，避免拆分为“过程/验证”。
  - 环境准备按任务需要调整，目标是可复现的初始状态。
  - 每个 case 的最后应提供一段 `sh` 伪代码。
  - 路径语义、错误语义与核心返回字段应与当前设计文档和真实实现保持一致，避免保留旧接口预期。
- 文档与实现关系：
  - 实现测试时严格遵循对应 `.md` 的步骤。
  - 若需要验证真实行为，优先构造真实文件、真实目录、真实 git 仓库和真实配置，并放到 `cli-tests/`。
  - 若需要验证 CLI 编排、参数传递、输出格式或懒加载，并依赖 mock / fake 数据，放到 `mock-cli-tests/`。
  - 若测试过程中发现 `.md` 逻辑有疑点，可反向更新 `.md` 保持一致性。
  - **非必要不改文档**；仅在逻辑冲突、步骤错误、预期失效时更新。
  - 若确需更新 `.md`，必须在文档变更中明确写清修改原因。
- 旧的 `tests/` 文件：
  - 不作为新规范样例。
  - 不作为评审验收依据。
  - 仅在迁移到 `cli-tests/` 时参考其历史行为。
- 仓库污染防护（特别是 rebuild/依赖变更测试）：
  - 涉及改写文件的用例必须包含对修改内容的还原。
  - 推荐使用 `try/finally` 做无条件回滚，避免异常中断导致脏工作区。

## 规范文档

- [目录职责说明](directory-responsibilities.md)：目录边界、依赖方向与归位规则。
- [架构概览与设计特点](architecture-overview.md)：分层结构、设计目标、能力沉淀路径与架构优势。
- [任务驱动沉淀](task-driven-iteration.md)：执行任务时沉淀工具与技能的流程规范。
- [CLI 交互统一设计](../design/chattool-cli-interaction-design.md)：统一 interactive 策略、TUI 模块边界与迁移顺序。
- [Mock CLI Tests](mock-cli-tests.md)：mock CLI 测试的目录边界、doc-first 规则与使用边界。
- [飞书能力设计](../design/feishu-cli.md)：`chattool lark` 与单目录 `skills/feishu/` 的目标形态。
