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
- setup 命令必须记录关键阶段日志。
- 入口层只做编排，不承载业务实现。

## 文档同步

- 工具能力：更新 `docs/tools/`
- 环境变量：更新 `docs/configuration.md`
- 开发规范：更新 `docs/development-guide/`
- 导航变更：同步更新 `mkdocs.yml`

## 测试与文档

- CLI 测试采用文档先行：先写 `cli-tests/*.md` 再实现对应 `.py`。
- 真实集成测试应标记为 `@pytest.mark.e2e`。
- 功能变更同步更新 `docs/` 与 `README.md`。
- 变更记录同步更新 `CHANGELOG.md`。

## 常用命令

```bash
python -m pytest -q
python -m build
mkdocs serve --no-livereload
```
