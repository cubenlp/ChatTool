---
name: feishu
description: Use the official `lark-cli` from `larksuite/cli` as the Feishu entrypoint. This skill is now a thin pointer to the upstream CLI and ChatTool docs.
version: 0.5.0
---

# Feishu Skill

这个目录现在只保留一个入口文件：`skills/feishu/SKILL.md`。

飞书相关工作默认直接使用官方 `lark-cli`，不再从仓库内主题 skill 文档开始：

- 上游仓库：`https://github.com/larksuite/cli`
- ChatTool 子模块：`lark-cli/`
- 仓库内教程：`docs/blog/agent-cli/lark-cli-guide.md`

## 默认路线

1. 先阅读 `docs/blog/agent-cli/lark-cli-guide.md`
2. 需要源码或固定版本时，直接使用仓库内的 `lark-cli/` 子模块
3. 优先使用官方三层命令体系：快捷命令 `+` -> API 命令 -> 原始 `api`

## 工作原则

- 飞书自动化优先复用官方 `lark-cli`，不要再为相同能力补一套平行 skill 文档
- 有副作用的操作先用 `--dry-run`，并尽量保持最小 scope
- 需要 Agent 协作登录时，优先用 `lark-cli auth login --no-wait` 和 `--device-code`
- ChatTool 内遗留的 `chattool lark` 只作为历史实现参考，不再是默认推荐入口

## 对应测试

- `cli-tests/lark/guide/test_chattool_lark_skill_index.md`
