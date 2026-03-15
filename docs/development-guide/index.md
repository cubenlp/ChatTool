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
- 统一解析顺序：`specific 参数 > default config file > environment variable`。
- 以模块化配置对象组织，支持按功能扩展。

### 3) `tools/`（核心能力）

- 每个工具目录负责该能力的完整实现。
- 同一工具应优先收敛三类接入：
  - Python API
  - CLI 命令
  - MCP 工具定义（如需要）
- CLI 交互体验通过通用策略层与 `utils/tui.py` 统一增强。

### 4) `skills/`

- 面向 Agent 的能力出口。
- 将工具能力按场景组织为可复用技能，不重复实现底层逻辑。

### 5) `setup/`

- 负责环境安装与配置初始化。
- 关键阶段必须可观测：开始、依赖检测、安装执行、配置写入、失败原因。
- 涉及 sudo 的操作默认输出可审阅指令，保持安全可回溯。

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

## CLI 开发规范

- 必要参数不完整时，自动触发 interactive。
- `-i` 强制 interactive，`-I` 强制非 interactive；参数不全时抛错。
- 参数提示读取默认值并显示脱敏内容（密钥必须 mask）。
- 贯彻最小 import，避免 CLI 启动性能退化。

## 文档组织

- `docs/index.md`：架构总览与快速入口。
- `docs/env/`：配置与环境管理规范。
- `docs/tools/`：工具使用与能力说明。
- `docs/development-guide/`：板块用途、边界规则、开发规范。
- `docs/blog/`：实践文章与经验沉淀。

## 规范文档

- [目录职责说明](directory-responsibilities.md)：目录边界、依赖方向与归位规则。
- [任务驱动沉淀](task-driven-iteration.md)：执行任务时沉淀工具与技能的流程规范。
