# ChatTool Python 库仓库构成设计

> 目标：基于当前仓库实际情况，明确一个适合发布到 PyPI 的 Python 库仓库构成，确保源码、CLI、文档、测试与发布边界清晰。

## 设计目标

- 保持标准 Python 打包方式，继续使用 `pyproject.toml` + `src/` 布局。
- 同时支撑三类交付物：Python API、CLI 命令、面向 Agent 的 skills。
- 让新增模块有明确归位规则，避免能力散落在根目录。
- 降低 PyPI 发布、文档构建、CLI 测试之间的耦合。

## 当前仓库现状

当前仓库已经具备一个可发布 Python 库的基础骨架：

- `pyproject.toml` 定义了项目元数据、依赖、可选依赖与 CLI 入口。
- `src/chattool/` 采用标准 `src` 布局，适合避免本地路径污染。
- `docs/` 使用 MkDocs 承载对外文档。
- `cli-tests/` 承载真实 CLI 的 doc-first 测试设计与真实执行实现。
- `mock-cli-tests/` 承载 mock CLI 的 doc-first 测试设计与执行实现。
- 仓库根下 `tests/` 仍有历史文件，但对 ChatTool 仓库自身已不再作为长期维护主线。
- `skills/` 存放可分发的技能模板与说明。

这套结构总体合理，但要把“工具仓库”进一步稳定成“Python 库仓库”，需要把各目录职责与发布边界写清楚。

## 推荐仓库构成

```text
ChatTool/
├── pyproject.toml          # 打包配置、依赖、入口脚本、可选依赖
├── README.md               # PyPI / GitHub 首页说明
├── CHANGELOG.md            # 版本变更记录
├── LICENSE                 # 开源协议
├── src/
│   └── chattool/
│       ├── __init__.py
│       ├── client/         # chattool CLI 入口与命令编排
│       ├── config/         # 配置读取、环境变量管理、chatenv
│       ├── llm/            # LLM 路由与会话抽象
│       ├── tools/          # 各工具核心实现
│       ├── mcp/            # MCP 服务入口与注册
│       ├── serve/          # 服务化能力
│       ├── setup/          # 环境安装与初始化
│       ├── skill/          # skill CLI 与安装逻辑
│       ├── docker/         # 容器模板与相关支持
│       └── utils/          # 稳定且可复用的通用辅助模块
├── tests/                  # 历史参考测试（弃用区，不再作为仓库主维护面）
├── cli-tests/              # CLI doc-first 测试文档与真实链路测试
├── mock-cli-tests/         # Mock CLI doc-first 测试文档与编排测试
├── docs/                   # MkDocs 文档
├── skills/                 # 可安装 skill 资产与说明
├── examples/               # 最小可运行示例
├── demo/                   # 面向演示的脚本或素材
└── .github/workflows/      # CI / 发布流程
```

## 顶层目录职责

### `pyproject.toml`

- 作为唯一打包入口。
- 维护 `project.dependencies`、`optional-dependencies`、`project.scripts`。
- 发布到 PyPI 的行为以该文件为准，不再分散到 `setup.py` 等旧配置。

### `src/chattool/`

- 这是唯一 Python 源码主目录。
- 对外可 import 的能力都应该从这里暴露。
- 新功能优先进入明确子目录，不在 `src/chattool/` 根下堆积业务文件。

### `cli-tests/`

- 这是 ChatTool 仓库中真实 CLI 测试的主线。
- 延续当前 doc-first 机制：先写 `.md`，再补 `.py`。
- `.md` 是测试设计与评审对象，`.py` 是真实执行实现。

### `mock-cli-tests/`

- 这是 ChatTool 仓库中 mock CLI 测试的主线。
- 同样采用 doc-first：先写 `.md`，再补 `.py`。
- `.md` 是 mock CLI 设计与评审对象，`.py` 是 mock 驱动的 CLI 编排测试实现。

### `tests/`

- 对 ChatTool 仓库自身，它是历史参考区，不再作为新开发默认维护面。
- 仅在迁移历史行为到 `cli-tests/` 时参考。
- 这一定义不影响 ChatTool 生成的外部 Python 包骨架继续使用自己的 `tests/` 目录。

### `docs/`

- 面向使用者与维护者的正式文档。
- 新工具、新环境变量、新开发规范都应落到对应栏目。
- 设计稿放在 `docs/design/`，用于沉淀尚未完全实现但需要先统一结构的方案。

### `skills/`

- 存放可分发、可安装的技能资产。
- 不直接承担 Python 包代码职责，避免与 `src/chattool/skill/` 混淆。
- 可以理解为“随仓库发布的业务资源”，不是 import 包主体。

## `src/chattool/` 内部分层建议

### 稳定层次

- `config/`、`llm/`、`utils/` 属于底层通用能力。
- `tools/` 是工具核心实现层。
- `client/`、`mcp/`、`serve/` 属于接入与编排层。
- `setup/`、`skill/`、`docker/` 属于交付与配套层。

### 依赖方向

推荐保持以下单向依赖：

```text
config / utils
    -> llm / tools
    -> client / mcp / serve
    -> setup / skill
```

约束：

- `tools/` 不依赖 `client/`。
- `mcp/` 只做协议适配，不复制工具实现。
- `client/` 只负责编排、参数解析、展示与交互。
- `utils/` 只保留足够通用的辅助逻辑，不变成杂项回收站。

## 作为 PyPI 包时的关键边界

### 1. 发布内容边界

- 发布主体是 `src/chattool/` Python 包。
- `docs/`、`cli-tests/`、`mock-cli-tests/`、`demo/`、`.github/` 不属于运行时包内容。
- `skills/` 是否进入 wheel/sdist，需要按“是否为安装后必需资源”单独判断。

当前建议：

- Python 运行时代码保持在 `src/chattool/`。
- 根目录 `skills/` 默认作为仓库资源管理；若未来需要安装后读取，再通过 package data 明确纳入。

### 2. CLI 入口边界

当前 `pyproject.toml` 已定义：

- `chattool = "chattool.client:main_cli"`
- `chatenv = "chattool.config.cli:cli"`
- `mcp-server-chattool = "chattool.mcp:main"`
- `chatskill = "chattool.skill.cli:main"`

这意味着仓库不是单纯 library，而是“library + CLI distribution”。设计上应继续保证：

- 核心逻辑可被 Python API 复用。
- CLI 入口只做薄封装，不把业务塞进命令文件。

### 3. 可选依赖边界

当前已经按 `dns`、`lark`、`images`、`browser`、`docs`、`tests`、`dev` 分组，这是正确方向。

建议继续遵循：

- 重依赖、平台依赖、第三方服务依赖进入 optional dependencies。
- 默认安装保持轻量，避免用户为了一个命令安装全部生态。
- 文档、测试、开发依赖与运行时依赖严格分离。

## 对当前仓库的收敛建议

### 建议保留

- 保留 `src/` 布局。
- 保留 `cli-tests/` 与 `mock-cli-tests/` 两条 CLI 测试线。
- 保留 `docs/` 与 `skills/` 的独立目录，不混入 Python 包源码。

### 建议约束

- 新工具一律先进入 `src/chattool/tools/<name>/`，再由 CLI/MCP 接入。
- 新 CLI 命令不要直接在根目录或 `client/main.py` 内堆积实现细节。
- `src/chattool/` 根目录只保留极少量公共入口文件，例如 `__init__.py`、`const.py`、聚合导出。

### 建议补强

- 持续清理 `__pycache__/`、`build/`、`*.egg-info` 这类构建产物，避免影响仓库阅读与提交。
- 对需要随包发布的非 Python 资源，统一评估是否放入 package data。
- 后续若引入更多子包，可以为 `tools/` 下各工具补更明确的对外 API 入口。

## 结论

对于 ChatTool 这类“既提供 Python API，又提供多命令 CLI 与配套 skills”的项目，当前最合适的仓库构成仍然是：

- 顶层使用 `pyproject.toml` 管打包与入口。
- 代码统一收敛到 `src/chattool/`。
- `cli-tests/`、`mock-cli-tests/`、`docs/`、`skills/` 作为独立配套目录；`tests/` 仅保留为历史参考区。

这能同时满足 PyPI 发布、CLI 演进、文档沉淀与 Agent 资产管理四类需求，并且与当前仓库现实结构基本一致，迁移成本最低。
