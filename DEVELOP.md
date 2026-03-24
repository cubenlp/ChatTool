# ChatTool 开发简版指南

## 代码结构

- 统一入口：`src/chattool/client/`
- 核心能力：`src/chattool/tools/`
- 协议入口：`src/chattool/mcp/`（实现下放 `tools/*/mcp.py`）
- 环境安装：`src/chattool/setup/`
- 远程服务：`src/chattool/serve/`
- Agent 技能：`src/chattool/skills/`

## 开发原则

- 新能力先落 `tools/<name>/`，再接入 `client/mcp/serve`。
- CLI 统一 `-i/-I` 与缺参自动交互规则。
- 所有 CLI 交互统一走 `utils/tui.py`。
- 进入 interactive 后，补全当前任务相关的关键参数。
- prompt 默认值必须与实际执行一致，敏感值默认脱敏。
- setup 命令必须记录关键阶段日志。
- 入口层只做编排，不承载业务实现。

## 文档同步

- 工具能力：更新 `docs/tools/`
- 环境变量：更新 `docs/configuration.md`
- 开发规范：更新 `docs/development-guide/`
- 导航变更：同步更新 `mkdocs.yml`

## 测试与文档

- ChatTool 仓库只长期维护 `cli-tests/` 这条测试主线。
- CLI 测试采用文档先行：先写 `cli-tests/*.md`，再实现对应 `.py`。
- `cli-tests/*.md` 是唯一长期维护的测试设计面；`cli-tests/*.py` 只作为真实 CLI 执行实现。
- 仓库根下 `tests/` 为弃用区，仅保留历史参考，不再作为新开发默认测试落点。
- 真实集成测试应标记为 `@pytest.mark.e2e`。
- 功能变更同步更新 `docs/` 与 `README.md`。
- 变更记录同步更新 `CHANGELOG.md`。
- 功能完成后按 `chattool-dev-review` 的口径做一次复查，至少检查 lazy import、缺参自动交互、`utils/tui.py` 统一交互，以及 docs / CHANGELOG / `cli-tests` 是否同步。

## 常用命令

```bash
python -m pytest -q
python -m build
mkdocs serve --no-livereload
```
