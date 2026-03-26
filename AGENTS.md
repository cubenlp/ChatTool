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
├── tools/      # 工具箱（dns、lark、image、network 等）
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
- 所有 CLI 交互统一走 `utils/tui.py`
- 进入 interactive 后，补全当前任务相关的关键参数
- interactive 展示的默认值必须与实际执行一致
- `-i` 进入当前命令交互流程，`-I` 完全禁用交互
- 目标明确的命令直接逐项提问；多板块、多分支命令优先先做选择页，再进入逐项补全
- **Lazy import**：import 放到函数内部，避免 CLI 启动变慢

### Setup

- setup 命令记录关键阶段日志（开始、依赖检测、安装执行、配置写入、失败原因）
- 出错时同时保留用户可读错误输出与 logger 错误记录

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

- **CLI 测试文档先行**：ChatTool 仓库内涉及 CLI 行为的开发，必须先写 `cli-tests/*.md`，再决定是否补对应 `.py`。
- **唯一长期维护的测试设计面**：`cli-tests/*.md` 是唯一长期维护的测试设计文档。
- **真实执行测试**：`cli-tests/*.py` 只作为对应 `.md` 的真实 CLI 执行实现；真实链路测试应标记为 `@pytest.mark.e2e`。
- **绝对禁止 mock**：宁可做范围更窄、更针对性的真实测试，也绝不允许用 mock 伪造行为。mock 对真实表现没有验收价值，且容易误导实现判断。
- **`tests/` 定位**：仓库根下 `tests/` 为弃用区，仅保留历史参考，不再作为新功能默认测试落点或交付要求。
- **第三方集成规则**：真实测试必须从默认 `chatenv` / 配置对象读取生效值，不允许通过 mock 伪装成真实链路。
- **文档更新**：功能变更必须同步更新 `docs/` 下的文档和 `README.md`。
- **变更记录**：每次功能或修复更新必须同步更新 `CHANGELOG.md`。
- **发版记录**：每次正式发版完成后，必须在仓库根目录 `release.log` 追加一条记录。

### CLI 测试文档驱动机制（`cli-tests`）

- `cli-tests` 作为 CLI 测试设计入口，采用 **doc-first**：
  - 先写 `.md`（测试目标、输入、执行顺序、预期）。
  - 文档评审通过后再实现对应 `.py`。
- ChatTool 仓库后续只维护 `cli-tests/` 这条测试主线；`tests/` 中的历史文件不再作为新规范依据。
- 命名规范（与 CLI 命令保持一致）：
  - 至少一个基础文件：`test_<cli>_<command>_basic.py`
  - 按主题扩展：`test_<cli>_<command>_<topic>.py`
  - 对应文档文件同名后缀 `.md`。
- 目录建议：
  - 命令目录下优先平铺（通过文件名区分 `basic/topic`），避免无必要的层级嵌套。
  - 例如：`cli-tests/chattool/dns/test_chattool_dns_basic.md`
  - 例如：`cli-tests/chattool/dns/test_chattool_dns_timeout.md`
- 文档结构建议：
  - 每个 case 优先保留“初始环境准备 / 预期过程和结果 / 参考执行脚本（伪代码）”结构。
  - 根据需要，可在 case 开头写必要的文字说明。
  - `预期过程和结果` 应按人类可理解顺序编写，把“执行了什么”和“紧接着预期什么”写在同一步里，避免拆分为“过程/验证”。
  - 环境准备按任务需要调整，目标是可复现的初始状态。
  - 每个 case 的最后应提供一段 `sh` 伪代码。
  - 路径语义、错误语义与核心返回字段应与当前设计文档和真实实现保持一致，避免保留旧接口预期。
- 文档与实现关系：
  - 实现测试时严格遵循对应 `.md` 的步骤。
  - 若需要测试某个真实行为，优先缩小测试范围、构造真实文件系统或真实仓库状态，不要引入 mock 层。
  - 若测试过程中发现 `.md` 逻辑有疑点，可反向更新 `.md` 保持一致性，但**非必要不改文档**。
  - 若确需更新 `.md`，必须在文档变更中明确写清修改原因。
- 旧的 `tests/` 文件：
  - 不作为新规范样例。
  - 不作为评审验收依据。
  - 仅在迁移到 `cli-tests/` 时参考其历史行为。
- 仓库污染防护（特别是 rebuild/依赖变更测试）：
  - 涉及改写文件的用例必须包含对修改内容的还原。
  - 推荐使用 `try/finally` 做无条件回滚，避免异常中断导致脏工作区。

### 提交规范

- 功能分支：`<username>/<feature>`
- commit 格式：`feat/fix/docs/refactor: <描述>`
- 版本号遵循 Semantic Versioning
