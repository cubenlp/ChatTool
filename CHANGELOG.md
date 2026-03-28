# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed
- env 配置机制开始切换为按类型拆分的目录模型：活动配置与 profile 现在按 `envs/<Config>/.env`、`envs/<Config>/<profile>.env` 管理，不再把单个全局 `.env` 作为唯一真相
- 配置优先级现调整为 `显式参数 > os.environ > env 文件 > 默认值`
- 对支持 `-e/--env` 的命令，配置优先级进一步固定为 `显式参数 > -e/显式 env > os.environ > 类型内置 .env > 默认值`，并写入配置文档与开发规范，便于后续统一复用
- `OpenAI` 配置移除了 `OPENAI_API_BASE_URL`，统一只保留 `OPENAI_API_BASE`
- `chattool lark` 现已从仓库内“平行飞书 CLI”收缩为最小遗留入口，只保留 `info`、`send`、`chat` 三个调试命令；原有文档、设计说明和大部分真实 CLI 测试已同步收口到这一边界
- `chattool setup playground` 现在默认使用工作区仓库目录名 `ChatTool/`；再次执行时会进入更新模式，优先更新现有仓库，并在交互模式下提示是否同步工作区 `skills/`
- `chattool setup playground` 同步 `skills/` 时现在只覆盖常规文件，继续保留各 skill 下的 `experience/` 目录和历史记录；历史工作区里的 `chattool/` 目录也会自动迁移到 `ChatTool/`
- `chattool setup playground` 现在会在 clone / 更新工作区仓库后自动执行 `git submodule update --init --recursive`，确保 `lark-cli/` 等子模块跟随仓库版本一起同步
- 仓库开发规范现在把“绝对禁止 mock”明确写入 `AGENTS.md`、`DEVELOP.md`、`docs/development-guide/` 与 `cli-tests/README.md`：宁可做更窄的真实测试，也不接受用 mock 伪造行为
- 开发规范现补充说明：GitHub 自动测试当前只覆盖 `.github/workflows/ci.yml` 里的 stable smoke tests，不包含 `lark` / `dns` 这类第三方链路与大多数真实 CLI 测试；相关能力需要本地单独验证
- `chattool gh pr-check` 现在支持 `--wait` 轮询等待 CI 结束；默认不设超时，只有显式传 `--timeout` 时才会超时报错
- `skills/feishu/` 现已收缩为单文件入口，只保留 `SKILL.md` 指向官方 `lark-cli` 与仓库内教程；原有专题 skill 文档与对应 doc-audit 测试一并清理
- `chattool pypi` 现已收口为最小命令集：只保留 `init/build/check/upload/probe`；移除 `doctor/publish/release`，并取消原有交互式补参与上传封装逻辑，`upload` 直接复用默认 `twine upload` 行为
- `chattool lark send` 现在把默认目标拆成“默认用户”和“默认群聊”两条路径：`FEISHU_DEFAULT_RECEIVER_ID` 继续用于用户消息，新增 `FEISHU_DEFAULT_CHAT_ID` 专门服务 `-t chat_id`
- Feishu 真实测试与文档说明现在回到生产口径，不再引入独立的 `FEISHU_TEST_USER_ID` / `FEISHU_TEST_USER_ID_TYPE`

### Fixed
- `chattool setup codex` 现在不再把实际 API key 错写进 `preferred_auth_method`：`config.toml` 中该字段固定为 `"apikey"`，真实密钥只写入 `auth.json` 的 `OPENAI_API_KEY`
- `chatenv new -t <type>` 在交互终端里不再退化成单纯的 `save` 语义：省略 profile 名时现在会先询问名称，再进入该类型字段填写，然后写入并激活新 profile
- `skills/feishu/` 补回 `SKILL.zh.md`，避免技能资产检查在 CI 中因缺少中文入口文件失败
- `chattool gh pr-merge` 新增可选的 `--check` 开关，用于在合并前显式检查 check runs 与 workflow runs，避免再次误把带红 CI 的 PR 当成可安全合并
- `chattool skill install` 不再强制要求 skill frontmatter 包含 `version`，只校验 `name` 与 `description`

### Added
- 新增根目录 `Dockerfile.playground`，用于直接构建一个最小的 ChatTool Playground 镜像；镜像在 `/opt/venv` 中安装 ChatTool，容器启动后会线性执行 `chattool setup playground -> chattool env set CHATTOOL_SKILLS_DIR -> chattool setup alias`
- `chatenv new <profile> -t <type>`，用于从当前激活的类型配置直接创建并激活一个新 profile，补齐 `save/use/delete` 之间的便捷新建入口
- `chattool gh run-view` 与 `chattool gh job-logs`，用于直接查看 GitHub Actions workflow run / job 详情与失败日志，避免排查 CI 时再临时写脚本
- `chattool setup codex -e ...` 现可显式复用 OpenAI 配置来源：支持 `.env` 文件路径或 `OpenAI` profile 名称，并按 `显式参数 > -e 指定的 oai 配置 > 当前 oai 配置 > 现有 codex 配置 > 默认值` 回退
- `chattool setup lark-cli`，用于安装官方 `lark-cli`，并按 `显式参数 > -e 指定的 feishu 配置 > 当前 feishu 配置 > 现有 lark-cli 配置 > 默认值` 复用 ChatTool 的 Feishu 配置；文档补充了 `~/.lark-cli/config.json` 与 ChatTool `envs/Feishu/.env` 的默认位置说明
- `chattool lark doc perm-public-get|perm-public-set` 与 `perm-member-list|perm-member-add`，补齐飞书文档权限读取、公开分享更新和显式协作者管理 CLI，避免再为“发出可编辑文档”临时写 SDK 脚本
- `skills/practice-make-perfact/references/cli-reference.md`，新增后处理阶段的 CLI 参考索引，方便在“手写脚本还是该补 CLI”之间快速做归位判断
- 博客新增 `docs/blog/agent-cli/lark-cli-guide.md`，整理官方 `larksuite/cli` 的安装、认证、三层命令体系与 Agent 场景下的安全使用路线
- `FEISHU_DEFAULT_CHAT_ID` 配置项，并补充默认群聊发送与 docx `openchat` 群权限的 quickstart 示例

## [6.4.0]

### Changed
- `chattool setup playground` 现在会在 workspace bootstrap 完成后，优先复用 `chatenv` 当前生效的 `GITHUB_ACCESS_TOKEN` 为 Git 配置 `https://github.com` 的 credential store；交互模式下也会提示是否配置并允许覆写 token
- `chattool cc init -i` 现在会在一开始先确认是否覆盖已有配置文件；已有平台配置和飞书凭证候选值会直接作为默认值展示，回车即可复用，不再追加“是否沿用默认”确认
- `chattool gh pr-view` 与 `chattool gh pr-check` 现在会直接显示 PR 的 `mergeable` / `mergeable_state`，避免只看到 head checks 却漏掉相对最新 base 的冲突态
- 飞书主 skill 现在重组为索引式技能包：根目录只保留 `skills/feishu/SKILL.md` 作为入口，专题说明、API 参考与 docx 边界统一收口到主题子目录
- `skills/feishu/guide/api-reference.md` 现在集中维护 Feishu 官方 API 文档 URL 与 `chattool lark` 到 API 的映射，便于扩展时继续学习与沉淀
- `chattool lark` 相关文档现在统一使用“双轨文档模型”描述云文档能力：稳定正文轨用于可靠写入，结构化 docx 轨用于 block 级增强
- `chattool lark scopes` 现在会在列出权限后补充关键能力分类摘要，并在匹配到未授权 scope 时直接标记为权限问题
- `chattool lark doc append-json` 现在会在写入前归一化 code block 的 `style.language` 字段，避免 `parse-md -> append-json` 因非法语言值整批失败
- `chattool lark troubleshoot check-scopes` 现在支持导出权限诊断卡片 JSON，并可直接把诊断卡片发给默认接收者或显式指定的目标
- CLI 入口现在统一过滤 `lark-oapi` 带来的 `pkg_resources` / event loop 噪音警告，且 `chattool lark` 改为按命令懒加载飞书实现，减少无关 import

### Added
- `FEISHU_TEST_USER_ID` 与 `FEISHU_TEST_USER_ID_TYPE` 配置项，用于 `chatenv cat -t feishu` 和 `@pytest.mark.lark` 真实测试共享测试用户配置
- `cli-tests/lark/guide/test_chattool_lark_basic.py`、`cli-tests/lark/documents/test_chattool_lark_doc_basic.py`、`cli-tests/lark/documents/test_chattool_lark_doc_markdown.py`，补齐 Feishu 基础链路与文档链路的真实 CLI 执行覆盖

### Removed
- 旧的文档读写型 Feishu skill `feishu-create-doc`、`feishu-fetch-doc`、`feishu-update-doc` 已并回主 `feishu` skill，不再单独维护

## [6.3.0]

### Changed
- `chattool setup playground` 现在在交互模式下遇到非空目录时会先提示是否继续；确认后会保留已有文件并继续初始化，且若 `chattool/` 已存在，会默认提示跳过克隆并保留本地版本，不再误走覆盖语义
- `chattool setup cc-connect` 现已提供 cc-connect 安装入口；`chattool cc setup` 改为该命令的别名，两者共用同一套安装逻辑
- `chattool setup codex` 默认模型现改为 `gpt-5.4`，`chattool setup claude` 默认小模型现改为 `claude-opus-4-6`
- `chattool setup codex` / `claude` / `opencode` 现在会在收集配置前先检查 `Node.js >= 20` 与 `npm`；若当前终端可交互且依赖不满足，会先提示是否执行 `chattool setup nodejs` 进行安装或升级
- `skills/practice-make-perfact` 现在改为任务完成后的后处理工作流：回顾已有改动、提取可复用内容、串联 `chattool-dev-review`，再统一完成文档/测试/变更记录与 PR/MR 收尾
- 开发流程现在明确要求把 scratch、临时试验产物与一次性导出结果放到仓库外独立目录，而不是放在仓库内
- `skills/chattool-gh` 现在覆盖 `pr-check`、PR 后续维护与 CI 排查流程，并同步更新为当前 GitHub CLI 用法
- `chattool setup playground` 现在可以在空目录下快速创建工作区：clone `chattool/`、生成 `AGENTS.md`/`CHATTOOL.md`/`MEMORY.md`、创建 `Memory/`/`skills/`/`scratch/`，并为复制出的每个 skill 建立 `experience/`
- `chattool setup nodejs` 现在改为写入仓库内置的 `nvm.sh` 与 shell 初始化块，不再通过 `curl` 从 GitHub 拉取 nvm 安装脚本
- `chattool cc init -i` 在选择飞书平台时，现会把当前 `chatenv` 中的 `FEISHU_APP_ID` / `FEISHU_APP_SECRET` 作为默认候选值
- `chattool skill` / `chatskill` 现在在未显式传 `--source` 时，会正确读取 `chatenv` 中的 `CHATTOOL_SKILLS_DIR`
- skill CLI 代码目录现统一为 `src/chattool/skill/`，避免与仓库根目录 `skills/` 资产目录混淆
- `chatenv init -t skill` 中 `CHATTOOL_SKILLS_DIR` 的交互提示已缩短，避免占用过多输入空间

### Fixed
- `cli-tests/env/test_chattool_env_basic.py` 现已补齐 `env init -t ...` 交互输入，避免因新增默认字段 prompt 导致测试中断
- 全量 `pytest` 现在可稳定完成：历史 `tests/tools/lark/test_cli_integration.py` 已改为唯一模块名，避免与 DNS 测试模块同名导致收集冲突
- `tests/dns/test_cert_server_real.py` 与 `tests/dns/test_cert_update_real.py` 现改为显式 `CHATTOOL_RUN_DNS_CERT_REAL=1` 才启用，避免日常全量回归卡在真实证书生命周期测试
- `tests/core/test_batch.py` 现已修正未 await 的协程调用，且 pytest 过滤规则补齐了常见第三方告警，降低全量回归噪音
- `chattool setup nodejs` 首次通过内置 `nvm` 安装 Node.js 后，后续同一轮 `setup codex/claude/opencode/cc-connect` 现在会正确复用 `~/.nvm` 中的运行时，不再误报 “Node.js requirement still not satisfied after setup”
- `chattool setup alias` 现在会把 `chatskill` 正确映射到 `chattool skill`

## [6.2.0]

### Added
- `chattool setup claude` — 安装 Claude Code CLI 并写入配置
- `chattool skill` / `chatskill` — Skills 管理，支持安装到 Codex / Claude Code
- 新增 skill：`chattool-dev-review`
- ChatTool skills 约定维护 `version` frontmatter，新建 skill 以 `0.1.0` 为初始版本
- 所有仓库内 skills 现在都提供对应的 `SKILL.zh.md`
- `chattool cc` — cc-connect 最小可用配置、启动与诊断命令
- `chattool skill install --prefix` — 安装时添加 `chattool-` 前缀
- `CHATTOOL_SKILLS_DIR` — 指定 skills 源目录
- 新增 skill：`feishu`
- `chattool cc init --full-options` — 提示填写代理等高级选项
- `chattool lark -e/--env` — 支持从指定 `.env` 文件或保存的 profile 读取飞书鉴权
- `chattool lark doc` — 支持飞书云文档创建、查询、纯文本读取、块查看与追加文本
- `chattool lark doc parse-md` — 支持将 Markdown 解析为飞书 docx block JSON，便于检查结构映射
- `chattool lark doc append-json` — 支持将结构化 block JSON 直接写入飞书云文档
- `chattool lark doc append-file` — 支持将本地 txt/md 文件整理后追加到飞书云文档
- `FEISHU_DEFAULT_RECEIVER_ID` — `chattool lark send` 可省略接收者并默认发给配置用户
- `chattool lark notify-doc` — 创建云文档、追加正文并把文档链接发送给默认用户
- `chattool lark notify-doc --append-file/--open` — 支持从文件追加正文并在成功后打开文档
- `chattool pypi` — 新增 Python 包 doctor/build/check/publish/release CLI
- `chattool pypi init` — 快速生成最小可发布的 `src/` 布局 Python 包骨架
- `chattool pypi probe` — 检查包名和版本在 PyPI/TestPyPI 上是否已被占用
- 文档：新增“Python 库仓库构成设计”，明确 PyPI 包、源码、测试、CLI 测试与 skills 的目录边界
- 设计：新增 `chattool pypi` CLI 文档，定义 build/check/publish/release 的命令边界与安全策略
- `chattool explore arxiv` — arXiv 论文搜索、daily 抓取与 preset 检索
- `chattool explore arxiv` 新增 `math-formalization-weekly` preset，并补充数学形式化近一周追踪 workflow
- `skills/arxiv-explore` 新增数学形式化近一周子模块，包含分类索引、真实样例和多查询收集脚本
- `chattool lark notify-doc --batch-size` — 批量写入失败时回退到单段追加，提升飞书文档写入稳定性
- 开发文档 `development-guide/architecture-overview.md`，系统说明 ChatTool 架构分层、设计特点与任务沉淀路径

### Fixed
- `chattool skill install` 现在会在安装前校验 `SKILL.md` 的 YAML frontmatter，并在缺少 `name`/`description` 时直接报错，避免把无效 skills 复制到 Codex / Claude Code
- `chattool skill install` 现在同时校验 `version` frontmatter，并要求使用 `0.1.0` 这类语义化版本格式
- `chattool setup nodejs` 现在会输出版本信息并在当前 shell 不可用时给出提示
- `chattool pypi init` 现在按统一 CLI 规范补全向导参数，并生成可直接运行 `python -m pytest -q` 的测试骨架
- `chattool pypi doctor/build/check/publish/release -i` 现在按统一 TUI 规范提示当前命令相关参数
- `chattool pypi init --version` 现在支持设置初始版本，并在 dynamic version 场景下解析真实版本值
- `chattool pypi publish/release` 现在优先复用 `.pypirc`，只有缺少配置时才回退到交互输入

## [5.3.0]

### Added
- 飞书机器人完整工具链：`LarkBot`、`ChatSession`、`MessageContext`
- CLI：`chattool lark`（发消息、上传、监听）、`chattool serve lark`（echo/ai/webhook）
- 支持 WebSocket 长连接和 Flask Webhook 两种接收模式
- 卡片消息、按钮回调、动态更新卡片

## [5.0.0]

### Added
- DNS 管理：统一接口支持阿里云和腾讯云
- DDNS 动态域名更新（公网 / 局域网）
- SSL 证书自动申请与续期（ACME v2 / DNS-01）
- 环境变量集中管理：`chatenv`，支持多 profile、敏感值打码

## [4.1.0]

### Changed
- 统一 `Chat` API（同步 / 异步 / 流式）
- 默认从环境变量读取 API 配置

## 更早版本

请参考仓库提交记录。
