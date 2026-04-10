# ChatTool 开发简版指南

## 代码结构

- 统一入口：`src/chattool/client/`
- 核心能力：`src/chattool/tools/`
- 模板型工具优先复用现有生成器风格，例如 `chattool docker`、`chattool nginx`
- 协议入口：`src/chattool/mcp/`（实现下放 `tools/*/mcp.py`）
- 环境安装：`src/chattool/setup/`
- 远程服务：`src/chattool/serve/`
- Agent 技能：`src/chattool/skills/`

## 开发原则

- 新能力先落 `tools/<name>/`，再接入 `client/mcp/serve`。
- CLI 统一 `-i/-I` 与缺参自动交互规则。
- 所有 CLI 交互统一走 `src/chattool/interaction/`。
- 新 CLI 默认优先使用 `src/chattool/interaction/command_schema.py` 里的 `CommandField` / `CommandSchema` / `CommandConstraint` / `resolve_command_inputs()` / `add_interactive_option()`，不要在每个命令里重复手写缺参判断、TTY 检查和补问流程。
- 对可恢复缺参，避免直接使用 Click 的 `required=True` 或必填位置参数；否则命令会在进入 callback 前被 Click 拦截，统一交互机制不会生效。
- 进入 interactive 后，补全当前任务相关的关键参数。
- prompt 默认值必须与实际执行一致，敏感值默认脱敏。
- 任何新增或修改的 CLI 都必须统一满足这些规则，不能只让当前命令局部符合。
- 若交互先做分类/模板选择，再逐项补参，文档、测试和实现顺序必须一致。
- CLI 顶层 import 保持最小化，执行期才需要的实现优先下沉到命令函数或局部 helper。
- 一级命令 help 也要校对：语言风格统一、描述不超出实际能力、group 子命令要带 short help。
- setup 命令必须记录关键阶段日志。
- 入口层只做编排，不承载业务实现。

## 文档同步

- 工具能力：更新 `docs/tools/`
- 环境变量：更新 `docs/configuration.md`
- 开发规范：更新 `docs/development-guide/`
- 导航变更：同步更新 `mkdocs.yml`
- 新工具落地后，同步更新 `README.md` / `README_en.md` / `AGENTS.md`

## 配置机制

- 默认优先级统一为：`显式参数 > 配置（若存在） > environment variable > ChatTool .env > default`
- 对支持 `-e/--env` 的命令，统一为：`显式参数 > -e/显式 env > 配置（若存在） > environment variable > ChatTool .env > default`
- profile 固定保存在 `envs/<Config>/<profile>.env`
- 新命令需要临时切换配置时，优先复用 `-e/--env`，不要再新增一套临时环境变量语义

## 测试与文档

- ChatTool 仓库长期维护两条 CLI 测试线：`tests/cli-tests/` 用于真实链路，`tests/mock-cli-tests/` 用于 mock 链路。
- CLI 测试采用文档先行：先写对应目录下的 `*.md`，再实现对应 `.py`。
- `tests/cli-tests/*.md` / `tests/cli-tests/*.py` 只维护真实 CLI 执行与验收。
- `tests/mock-cli-tests/*.md` / `tests/mock-cli-tests/*.py` 只维护基于 mock 的 CLI 编排测试。
- 所有使用 `mock`、`patch`、`monkeypatch`、fake client、fake API 的 CLI 测试，必须收纳到 `tests/mock-cli-tests/`。
- GitHub 自动测试当前只覆盖 `.github/workflows/ci.yml` 里的 stable smoke tests，不包含 `lark` / `dns` 这类第三方链路与大多数 `@pytest.mark.e2e` 用例；相关能力必须在本地按文档单独验证。
- `tests/code-tests/` 用于非 CLI 代码测试与历史测试迁移；不要再把新的 CLI 测试直接写到这个目录。
- 真实集成测试应标记为 `@pytest.mark.e2e`。
- 功能变更同步更新 `docs/` 与 `README.md`。
- 变更记录同步更新 `CHANGELOG.md`。

## 常用命令

```bash
python -m pytest -q
python -m build
mkdocs serve --no-livereload
```
