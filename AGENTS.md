# ChatTool Agent Notes

## 项目信息

- 主语言：Python
- CLI 入口：`chattool`、`chatenv`、`chatskill`
- 代码路径：`src/chattool/`
- Skills CLI 代码目录：`src/chattool/skill/`
- 文档：`docs/`，用 mkdocs-material 构建

## 板块结构

```
src/chattool/
├── client/     # 统一 CLI 主入口（chattool）
├── llm/        # LLM 路由、Chat 对象
├── config/     # 环境变量管理（chatenv）
├── tools/      # 工具箱（dns、lark、image、network、nginx 等）
├── mcp/        # MCP 入口与编排（工具实现下放到 tools/*/mcp.py）
├── setup/      # 环境安装脚本
├── serve/      # 服务端（截图、证书分发等）
└── skill/      # skill CLI 与相关能力
```

## 常用命令

```bash
python -m pytest -q          # 运行测试
python -m build              # 构建包
mkdocs serve --no-livereload # 本地预览文档
```

## 开发规范

### CLI

- 必要参数缺失时自动触发 interactive 模式
- `-i` 强制开启交互，`-I` 强制关闭（参数不全则报错）
- 参数默认值从环境变量读取，敏感值在提示中自动 mask
- 所有 CLI 交互统一走 `src/chattool/interaction/`
- 新 CLI 默认优先使用 `src/chattool/interaction/command_schema.py` 里的 `CommandField` / `CommandSchema` / `CommandConstraint` / `resolve_command_inputs()` / `add_interactive_option()`，不要在每个命令里重复手写缺参判断、TTY 检查和 prompt 流程
- 对可恢复缺参，避免直接使用 Click 的 `required=True` 或必填位置参数；否则会在 callback 执行前被 Click 拦截，统一交互机制无法运行
- 进入 interactive 后，补全当前任务相关的关键参数
- interactive 展示的默认值必须与实际执行一致
- `-i` 进入当前命令交互流程，`-I` 完全禁用交互
- 目标明确的命令直接逐项提问；多板块、多分支命令优先先做选择页，再进入逐项补全
- **Lazy import**：import 放到函数内部，避免 CLI 启动变慢

### Setup

- setup 命令记录关键阶段日志（开始、依赖检测、安装执行、配置写入、失败原因）
- 出错时同时保留用户可读错误输出与 logger 错误记录
- 若 setup 流程涉及 `sudo` 命令，必须提供显式 `--sudo` 开关；未指定 `--sudo` 时，无论非交互还是交互未确认，都只打印建议命令，由用户自行处理
- setup 类命令若同时支持显式参数、`-e/--env`、已有工具配置、环境变量与 ChatTool `.env`，统一优先级必须为：`显式参数 > -e/--env > 工具默认配置位置 > 系统环境变量 > ChatTool .env > 默认值`

### 工具结构

每个工具放 `tools/<name>/`，包含：

- `__init__.py` — 对外暴露的 Python API
- `cli.py` — CLI 命令（接入 `chattool <name>`）
- `mcp.py` — MCP 工具定义（如有）

### 文档

- 新增 CLI 或工具：同步更新 `docs/tools/<name>/index.md`
- 新增环境变量：同步更新 `docs/configuration.md`
- 开发规范与目录边界：同步更新 `docs/development-guide/`
- 新增板块：在 `mkdocs.yml` nav 中注册，并更新本文件与 `DEVELOP.md`

### 测试与文档

- **CLI 测试文档先行**：ChatTool 仓库内涉及 CLI 行为的开发，必须先写测试设计文档，再决定是否补对应 `.py`。
- **双轨测试面**：
  - `tests/cli-tests/*.md` / `tests/cli-tests/*.py`：真实 CLI 链路与真实环境验收。
  - `tests/mock-cli-tests/*.md` / `tests/mock-cli-tests/*.py`：基于 mock 的 CLI 编排、参数流向、输出格式与懒加载验证。
- **真实执行测试**：`tests/cli-tests/*.py` 只作为对应 `.md` 的真实 CLI 执行实现；真实链路测试应标记为 `@pytest.mark.e2e`。
- **Mock 收纳规则**：所有使用 `mock`、`patch`、`monkeypatch`、fake client、fake API 的 CLI 测试，都必须收纳到 `tests/mock-cli-tests/`，不要继续放在 `tests/cli-tests/`。
- **GitHub 自动测试边界**：当前 `.github/workflows/ci.yml` 只跑 stable smoke tests，不包含 `lark` / `dns` 这类第三方链路与大多数真实 CLI 测试；本地验证不能省。
- **`tests/code-tests/` 定位**：`tests/code-tests/` 用于非 CLI 代码测试与历史测试迁移，不作为新 CLI 测试默认落点。
- **第三方集成规则**：真实测试必须从默认 `chatenv` / 配置对象读取生效值；若改用 mock 验证，只能放到 `tests/mock-cli-tests/`，不能伪装成真实链路。
- **文档更新**：功能变更必须同步更新 `docs/` 下的文档和 `README.md`。
- **变更记录**：每次功能或修复更新必须同步更新 `CHANGELOG.md`。
- **发版记录**：每次正式发版完成后，必须在仓库根目录 `release.log` 追加一条记录。

### CLI 测试文档驱动机制（`tests/cli-tests` / `tests/mock-cli-tests`）

- `tests/cli-tests` 与 `tests/mock-cli-tests` 都采用 **doc-first**：
  - 先写 `.md`（测试目标、输入、执行顺序、预期）。
  - 文档评审通过后再实现对应 `.py`。
- `tests/cli-tests/` 只维护真实 CLI 测试；`tests/mock-cli-tests/` 只维护 mock CLI 测试；`tests/code-tests/` 中的历史/代码测试不作为 CLI 规范依据。
- 命名规范（与 CLI 命令保持一致）：
  - 至少一个基础文件：`test_<cli>_<command>_basic.py`
  - 按主题扩展：`test_<cli>_<command>_<topic>.py`
  - 对应文档文件同名后缀 `.md`。
- 目录建议：
  - 命令目录下优先平铺（通过文件名区分 `basic/topic`），避免无必要的层级嵌套。
  - 例如：`tests/cli-tests/dns/test_chattool_dns_basic.md`
  - 例如：`tests/mock-cli-tests/gh/test_chattool_gh_basic.md`
- 文档结构建议：
  - 每个 case 优先保留“初始环境准备 / 预期过程和结果 / 参考执行脚本（伪代码）”结构。
  - 根据需要，可在 case 开头写必要的文字说明。
  - `预期过程和结果` 应按人类可理解顺序编写，把“执行了什么”和“紧接着预期什么”写在同一步里，避免拆分为“过程/验证”。
  - 环境准备按任务需要调整，目标是可复现的初始状态。
  - 每个 case 的最后应提供一段 `sh` 伪代码。
  - 路径语义、错误语义与核心返回字段应与当前设计文档和真实实现保持一致，避免保留旧接口预期。
- 文档与实现关系：
  - 实现测试时严格遵循对应 `.md` 的步骤。
  - 若需要测试某个真实行为，优先缩小测试范围、构造真实文件系统或真实仓库状态，放到 `tests/cli-tests/`。
  - 若需要验证 CLI 编排、参数传递、输出格式或懒加载，并依赖 mock / fake 数据，放到 `tests/mock-cli-tests/`。
  - 若测试过程中发现 `.md` 逻辑有疑点，可反向更新 `.md` 保持一致性，但**非必要不改文档**。
  - 若确需更新 `.md`，必须在文档变更中明确写清修改原因。
- `tests/code-tests/` 中的旧测试：
  - 不作为新 CLI 规范样例。
  - 不作为 CLI 评审验收依据。
  - 仅在迁移真实/模拟 CLI 测试时参考其历史行为。
- 仓库污染防护（特别是 rebuild/依赖变更测试）：
  - 涉及改写文件的用例必须包含对修改内容的还原。
  - 推荐使用 `try/finally` 做无条件回滚，避免异常中断导致脏工作区。

### 提交规范

- 功能分支：`<username>/<feature>`
- commit 格式：`feat/fix/docs/refactor: <描述>`
- 版本号遵循 Semantic Versioning
