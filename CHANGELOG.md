# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- `chattool setup claude` — 安装 Claude Code CLI 并写入配置
- `chattool skill` / `chatskill` — Skills 管理，支持安装到 Codex / Claude Code

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
