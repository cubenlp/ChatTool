---
name: practice-make-perfact
description: ChatTool 仓库任务的后处理工作流。适用于任务实现完成后，回顾已有改动、先检查现有 CLI 是否已覆盖、提取可复用内容落回仓库、调用 $chattool-dev-review 做开发验收，并按规范补齐文档/测试/变更记录与 PR/MR 流程；若任务还包含合并后的正式发版，则在 PR/MR 阶段后切到 $chattool-release。
version: 0.4.1
---

# Practice Make Perfact（中文）

这是 ChatTool 仓库的后处理阶段 skill。

适用于 ChatTool 仓库里的功能开发、修复、重构、CLI 变更、skill 更新，以及任何已经基本完成、准备进入规范化收尾的任务。

核心思路：先把任务做完，再显式进入后处理阶段，回顾现有产物、提取有价值内容沉淀进仓库，并按规范走完 review 与提交流程。

## 核心原则

- 先做事，再整理：先把任务完成，再统一规范与复盘。
- 能复用进 `src/` 的能力就进 `src/`；仅任务相关的就放 `skills/`。
- 过程尽量用 CLI，保持可审计、可复现。
- 每个任务结束后必须进入一次后处理 review 阶段。
- 默认目标不是“本地改完就停”，而是推进到 PR/MR 阶段。
- 这个 skill 不负责前期探索，不要在开工前把它当作流程门槛。

## 执行流程

1. **只在任务基本完成后进入**  
   - 不把这份 skill 当作开工前提醒  
   - 主任务已经做完或至少主路径已打通后，再主动调用它  
   - 把它视为一个明确的后处理阶段

2. **先回顾已有产物**  
   - 阅读当前 diff、改动文件和任务过程中产生的中间产物  
   - 区分哪些是临时探索材料，哪些值得沉淀到仓库  
   - 临时脚本、试验输出、探索草稿继续留在仓库外目录，例如 `~/tmp/chattool/<task>/`

3. **提取并归位可复用内容**  
   - 通用能力：补充到 `src/`（工具层、CLI、MCP）  
   - 任务特定：补充到 `skills/<name>/`
   - 只有需要长期保留的结果，才整理后放回仓库里的正式位置
   - 统一命名、目录和职责边界，避免“任务做完了，但沉淀位置还是临时的”
   - 在决定保留临时脚本前，先检查现有 CLI 是否已经覆盖类似动作
   - 这一步先看 `references/cli-reference.md`，再决定是补 CLI 还是保留为一次性探索

4. **任务后强制 review**  
   - 默认 review 当前 diff，而不是整个仓库  
   - 检查最小 import / lazy import  
   - 检查缺参自动交互与 `-i/-I`  
   - 检查新的交互是否统一走 `utils/tui.py`  
   - 检查测试、`docs/`、`README.md`、`CHANGELOG.md`、`cli-tests/` 是否同步  
   - 默认主动调用 `$chattool-dev-review` 做这一轮开发验收，除非用户明确不要

5. **文档与 skill 同步**  
   - 在 `docs/` 补充或更新相关说明  
   - 用户可见变更同步更新 `README.md`  
   - 更新 `CHANGELOG.md`  
   - 如果这次任务要作为某个正式包版本发出，必须在 PR/MR 阶段前就把 `src/chattool/__init__.py` bump 到目标版本，而不是合并后再改
   - skill 变更时，维护 `SKILL.md` 与 `SKILL.zh.md`  
   - skill frontmatter 中的 `version` 要同步维护

6. **一直推进到 PR/MR 阶段**  
   - 确保分支已经 commit 并 push  
   - 用 `chattool gh` 执行 GitHub PR 相关操作  
   - 默认使用 `chattool gh pr-create --body-file ...` 建 PR  
   - 若范围变化，继续更新 PR 内容  
   - 任务默认停在 PR/MR 阶段，而不是停在本地提交

7. **正式发版动作单独切阶段**  
   - 如果任务还包括版本 tag、`Publish Package`、PyPI 校验或 `release.log`，在 PR/MR 阶段后切到 `$chattool-release`
   - 把“开发后整理”与“合并后发版”视为两个阶段
   - 不要因为实现已经 ready，就从未合并分支直接打 tag
   - 如果 PyPI 已经有该版本，不要试图重推同版本 tag 解决问题；正确动作是回到新的 PR，先把版本号 bump 到下一个版本

8. **只有明确要求时才提前停下**  
   - 如果用户明确只要分析、只要方案、只做到一半，就按用户要求停  
   - 否则默认走完整个“后处理整理 -> review -> PR”流程

## 结果要求

- 每次任务都能沉淀到工具、技能或文档。
- 阶段化输出与命名一致，便于检索与复用。
- 这份 skill 应服务于任务结束后的回顾与沉淀，而不是前期探索。
- 它应明确串联 `$chattool-dev-review`，帮助模型按开发规范做收尾。
- 如果用户明确要求正式发版，它应把该阶段切给 `$chattool-release`。
- 默认落点应是已经进入 PR/MR 阶段的结果。
- 它还应提供一个很轻的 CLI 参考面，帮助模型快速判断“该继续手写脚本，还是应该补一个正式命令”。
