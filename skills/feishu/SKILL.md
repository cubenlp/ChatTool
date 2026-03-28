---
name: feishu
description: Use the official `lark-cli` from `larksuite/cli` as the Feishu entrypoint. For document work, split body edits to `docs`, comments and permissions to `drive`, wiki resolving to `wiki`, and keep `chattool lark` only for the shortest debug and delivery path.
version: 0.6.0
---

# Feishu Skill

这个目录现在只保留一个入口文件：`skills/feishu/SKILL.md`。

飞书相关工作默认直接使用官方 `lark-cli`，不再从仓库内主题 skill 文档开始：

- 上游仓库：`https://github.com/larksuite/cli`
- ChatTool 子模块：`lark-cli/`
- 仓库内教程：`docs/blog/agent-cli/lark-cli-guide.md`
- 文档实践博客：`docs/blog/agent-cli/feishu-cli-doc-practice.md`

## 默认路线

1. 先阅读 `docs/blog/agent-cli/lark-cli-guide.md`
2. 需要源码或固定版本时，直接使用仓库内的 `lark-cli/` 子模块
3. 优先使用官方三层命令体系：快捷命令 `+` -> API 命令 -> 原始 `api`

## 文档工作流怎么拆

对于文档相关任务，先按这个命令面拆：

- 正文内容：`lark-cli docs +create` / `+fetch` / `+update`
- 评论与权限：`lark-cli drive +add-comment` / `file.comment.replys` / `file.comments` / `permission.members`
- wiki 节点解析：`lark-cli wiki spaces get_node`
- 最后送达和最短调试：`chattool lark info` / `send` / `chat`

如果任务落在“创建文档 -> 更新正文 -> 留评论 -> 授权 -> 把链接发给人”这条链上，不要回到旧的 `chattool lark` 文档子命令。

## 当前已验证的实践边界

这些结论已经在仓库当前文档实战里跑过，可先按默认假设使用：

- `docs +create / +fetch / +update` 可以走 `--as bot`
- `drive +add-comment`、`drive file.comment.replys create`、`drive permission.members create` 可以走 `--as bot`
- `docs +search` 实测应视为 `user`-only
- 评论刚创建后，`file.comments list` 可能需要短暂重试
- shell 里不要用带字面量 `\\n` 的字符串硬拼 Markdown，优先用真实换行或 heredoc

## 默认决策规则

1. 安装或迁移配置：先用 `chattool setup lark-cli`
2. 最短本地调试：才用 `chattool lark`
3. 已知 doc URL/token 的自动化：先尝试 bot 路线
4. 搜索、发现、浏览：预期需要 user 身份
5. `/wiki/...` 链接不要直接当 doc token，用 `wiki spaces get_node` 先解析真实对象

## 工作原则

- 飞书自动化优先复用官方 `lark-cli`，不要再为相同能力补一套平行 skill 文档
- 有副作用的操作先用 `--dry-run`，并尽量保持最小 scope
- 需要 Agent 协作登录时，优先用 `lark-cli auth login --no-wait` 和 `--device-code`
- ChatTool 内遗留的 `chattool lark` 现在只保留 `info`、`send`、`chat` 三个最小调试命令，不再是默认推荐入口

## 对应测试

- `cli-tests/lark/guide/test_chattool_lark_skill_index.md`
