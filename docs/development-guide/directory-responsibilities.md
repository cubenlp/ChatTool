# 目录职责说明

本文档定义 ChatTool 主要目录的职责边界，作为架构分层与代码归位的执行基线。

## 职责边界

### `src/chattool/config/`

- 负责环境变量加载、配置解析与默认值治理。
- 对上层提供统一配置读取接口，避免业务代码直接操作 `os.environ`。
- 不承载工具业务逻辑。

### `src/chattool/llm/`

- 负责模型路由、会话对象与响应封装。
- 对外提供稳定的 LLM 调用 API。
- 不承载具体工具能力实现。

### `src/chattool/tools/`

- 负责工具核心能力实现，是工具逻辑唯一归属层。
- 每个工具目录负责能力实现与能力编排，不跨目录复制逻辑。
- 对外暴露 Python API，供 CLI、MCP、Serve 等层复用。

### `src/chattool/client/`

- 负责 `chattool` 统一命令入口、参数路由与命令编排。
- 只做接入、编排与展示，不实现底层工具核心逻辑。
- 遵循缺参自动交互与 `-i/-I` 统一行为规范。

### `src/chattool/mcp/`

- 负责 MCP 服务入口、工具注册与能力分发。
- 只做协议层适配，不重复实现工具细节。
- 工具实现下放到 `src/chattool/tools/*/mcp.py`。

### `src/chattool/serve/`

- 负责远程服务侧能力承载与服务化接口。
- 适配密钥敏感或算力敏感场景。
- 与 `client/` 保持调用边界，不反向耦合业务入口。

### `src/chattool/setup/`

- 负责安装脚本与运行环境准备。
- 提供可审阅、可复现的环境准备流程。
- 不承载业务工具能力实现。

### `src/chattool/docker/`

- 负责 docker 模板生成、示例参数与部署配置组织。
- 为 setup 与工具运行环境提供容器化入口。

### `src/chattool/skills/`

- 负责面向 Agent 的能力封装与场景化组织。
- 聚合已存在能力，不重复实现底层工具。

### `docs/`

- 负责功能说明、规范沉淀与执行约束公开。
- 新增能力时同步维护对应章节，保持文档与实现一致。

## 协作规则

- 能力新增优先进入 `tools/<name>/`，再由 `client/mcp/serve` 进行接入。
- 跨层调用遵循单向依赖：`config/setup -> llm/tools -> client/mcp/serve -> skills`。
- 若目录职责冲突，以本文件与 `docs/development-guide/index.md` 为准统一收敛。
