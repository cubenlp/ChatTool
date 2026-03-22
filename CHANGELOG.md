# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `chattool setup claude` — 安装 Claude Code CLI 并写入配置
- `chattool skill` / `chatskill` — Skills 管理，支持安装到 Codex / Claude Code
- `chattool cc` — cc-connect 最小可用配置、启动与诊断命令
- `chattool skill install --prefix` — 安装时添加 `chattool-` 前缀
- `CHATTOOL_SKILLS_DIR` — 指定 skills 源目录
- 新增 skill：`feishu`
- `chattool cc init --full-options` — 提示填写代理等高级选项
- `chattool lark -e/--env` — 支持从指定 `.env` 文件或保存的 profile 读取飞书鉴权
- `chattool lark doc` — 支持飞书云文档创建、查询、纯文本读取、块查看与追加文本
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

### Fixed
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
