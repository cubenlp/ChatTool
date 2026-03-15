# ChatTool Agent Notes

## 项目信息

- 主语言：Python
- CLI 入口：`chattool`、`chatenv`、`chatskill`
- 代码路径：`src/chattool/`
- Skills 目录：`src/chattool/skills/`
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
└── skills/     # skills CLI 与相关能力
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
- **最小 import**：import 放到函数内部，避免 CLI 启动变慢

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

### 提交规范

- 功能分支：`rex/<feature>`
- commit 格式：`feat/fix/docs/refactor: <描述>`
- 版本号遵循 Semantic Versioning
