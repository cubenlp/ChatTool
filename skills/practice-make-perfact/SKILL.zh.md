---
name: practice-make-perfact
description: ChatTool 开发任务后处理工作流：更新项目 PRD/progress，沉淀 durable 产物，检查已有 CLI，运行 dev review，并完成 docs/tests/changelog/PR 收尾。
version: 0.5.0
---

# Practice Make Perfact

在 ChatTool 的功能、修复、重构、CLI 变更、skill 更新或带文档的行为变更基本完成后使用这个 skill。

这是任务后的规范化收尾流程，不是开工前探索指南。

## 工作流

1. 回顾实际产物
   - 阅读当前 diff、改动文件和生成结果。
   - 区分 durable 仓库产物和临时探索材料。
   - 临时探索默认留在仓库外，除非需要整理成长期维护文档。

2. 先更新项目内记录
   - 如果任务发生在 `projects/<date>-<name>/` 下，先更新该项目的 `PRD.md`、`progress.md` 和 `memory.md`。
   - 不要把一次性原始调研直接提升到 workspace 根 reference。
   - 只有规范化后的 durable 产物才进入 ChatTool 的 `src/`、`docs/`、`skills/` 或 `tests/`。

3. 新增脚本前先查已有 CLI
   - 先看 `references/cli-reference.md`。
   - 优先复用已有 `chattool pypi`、`chatpypi`、`chattool skill`、`chatenv`、`chatgh` 和 `chatdns` 命令。
   - 只有当动作可复用、容易出错且现有 CLI 没覆盖时，才考虑新增脚本。

4. 规范 ChatArch 边界
   - ChatTool 命令需要本项目 policy 或测试 patch 点时使用 `chattool.interaction` adapter。
   - 独立 ChatArch 包直接使用外部 `chatstyle` 与 `chatenv`。
   - 新 env/profile schema 应作为 provider module，并通过 `chatenv.configs` 注册。

5. 规范 skills
   - skill 变更必须保持 `SKILL.md` 和 `SKILL.zh.md` 对齐。
   - 如果 skill 有 `agents/openai.yaml`，行为或触发范围变化时同步更新 metadata。
   - 新 skill 通常应包含英文、中文说明和 agents metadata。
   - skill 编辑后运行旧命令 grep。

6. 运行任务后 review
   - 默认 review 当前 diff，而不是全仓。
   - 检查 lazy import、`-i/-I` 交互、ChatStyle/ChatEnv 边界、docs、tests、README 和 changelog。
   - 除非用户明确不要，否则使用 `$chattool-dev-review`。

7. 推进到 PR/MR 阶段
   - commit 并 push 当前分支。
   - 使用 `chatgh` 做 GitHub 读取/检查操作，例如 `pr view`、`pr checks`、`run view`、`run logs`。
   - PR 创建或正文更新在 ChatGH 公开写命令前，使用项目当前 GitHub workflow 或 API 路径。
   - 交付需要 CI 状态时，在 GitHub checks 到达终态后查询 `chatgh pr checks <pr> --repo owner/repo`。

8. 正式发版单独交接
   - tag、包发布和 PyPI 校验属于合并后的 `$chattool-release`。
   - 不要从未合并 PR head 直接打 tag。
   - 版本号必须在 PR/MR 阶段前完成 bump，而不是合并后再改。
   - 如果 PyPI 已经存在目标版本，先把版本号 bump 到下一个版本并重新走 PR。

## 结果要求

- 仓库 diff 已归一到维护位置。
- 存在项目内 `PRD.md` / `progress.md` / `memory.md` 时已更新。
- skills 有匹配的英文和中文文件。
- 行为变更同步 docs/tests/changelog。
- 除非用户明确要求提前停止，否则任务推进到 PR/MR 阶段。
