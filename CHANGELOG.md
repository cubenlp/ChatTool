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
- `chattool lark doc parse-md` — 支持将 Markdown 解析为飞书 docx block JSON，便于检查结构映射
- `chattool lark doc append-json` — 支持将结构化 block JSON 直接写入飞书云文档
- `chattool lark doc append-file` — 支持将本地 txt/md 文件整理后追加到飞书云文档
- `FEISHU_DEFAULT_RECEIVER_ID` — `chattool lark send` 可省略接收者并默认发给配置用户
- `chattool lark notify-doc` — 创建云文档、追加正文并把文档链接发送给默认用户
- `chattool lark notify-doc --append-file/--open` — 支持从文件追加正文并在成功后打开文档
- `chattool lark notify-doc --batch-size` — 批量写入失败时回退到单段追加，提升飞书文档写入稳定性
- 开发文档 `development-guide/architecture-overview.md`，系统说明 ChatTool 架构分层、设计特点与任务沉淀路径

### Fixed
- `chattool setup nodejs` 现在会输出版本信息并在当前 shell 不可用时给出提示

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
