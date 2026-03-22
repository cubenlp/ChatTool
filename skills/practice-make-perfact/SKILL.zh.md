---
name: practice-make-perfact
description: ChatTool 仓库任务的默认开发流程。适用于任何 ChatTool 实现任务：前期只做轻量提醒，不干扰探索；当实现方向明确后，再严格完成 review、文档/测试/变更记录同步，并使用 chattool gh 推进到 PR/MR 阶段。
version: 0.1.0
---

# Practice Make Perfact（中文）

这是 ChatTool 仓库的默认开发流程 skill。

适用于 ChatTool 仓库里的功能开发、修复、重构、CLI 变更、skill 更新，以及任何需要最终进入 PR/MR 阶段的任务。

核心思路：前期探索尽量轻约束，方向明确后再严格走完规范化和提交流程，直到进入 PR/MR 阶段。

## 核心原则

- 先做事，再整理：先把任务完成，再统一规范与复盘。
- 能复用进 `src/` 的能力就进 `src/`；仅任务相关的就放 `skills/`。
- 过程尽量用 CLI，保持可审计、可复现。
- 每个任务结束后必须做一次规范化 review。
- 默认目标不是“本地改完就停”，而是推进到 PR/MR 阶段。
- 但前期探索、读代码、定方案时，不要被流程本身过度打断。

## 执行流程

1. **任务执行优先**  
   - 在 ChatTool 仓库里做任务时，先看这份 skill  
   - 然后把注意力切回具体任务本身  
   - 优先直接执行，不要在任务没完成前过度讨论流程  
   - 用 CLI 完成读取、查询和导出，保持可复现
   - 在这个阶段，这份 skill 只做轻量提醒，不要过度干扰探索
   - 临时脚本、试验输出、探索草稿优先放到 `playground/`

2. **能力归类**  
   - 通用能力：补充到 `src/`（工具层、CLI、MCP）  
   - 任务特定：补充到 `skills/<name>/`

3. **先完成实现，再做规范化**  
   - 先让功能、修复或内容变更真正可用  
   - 不要在未完成状态下过度补文档
   - 只要方案还在探索期，就不要急着强推完整流程

4. **方向明确后再切换到强流程**  
   - 一旦实现方向、改动边界或方案已经明确，就进入完整规范化流程  
   - 这时再严格执行 review、文档同步和 PR 流程

5. **任务后强制 review**  
   - 默认 review 当前 diff，而不是整个仓库  
   - 检查最小 import / lazy import  
   - 检查缺参自动交互与 `-i/-I`  
   - 检查新的交互是否统一走 `utils/tui.py`  
   - 检查测试、`docs/`、`README.md`、`CHANGELOG.md`、`cli-tests/` 是否同步  
   - 需要时调用 `$chattool-dev-review`

6. **文档与 skill 同步**  
   - 在 `docs/` 补充或更新相关说明  
   - 用户可见变更同步更新 `README.md`  
   - 更新 `CHANGELOG.md`  
   - skill 变更时，维护 `SKILL.md` 与 `SKILL.zh.md`  
   - skill frontmatter 中的 `version` 要同步维护
   - 只有需要长期保留的结果才从 `playground/` 迁出

7. **一直推进到 PR/MR 阶段**  
   - 确保分支已经 commit 并 push  
   - 用 `chattool gh` 执行 GitHub PR 相关操作  
   - 默认使用 `chattool gh pr-create --body-file ...` 建 PR  
   - 若范围变化，继续更新 PR 内容  
   - 任务默认停在 PR/MR 阶段，而不是停在本地提交

8. **只有明确要求时才提前停下**  
   - 如果用户明确只要分析、只要方案、只做到一半，就按用户要求停  
   - 否则默认走完整个“任务执行 -> review -> PR”流程

## 结果要求

- 每次任务都能沉淀到工具、技能或文档。
- 阶段化输出与命名一致，便于检索与复用。
- 前期探索应保持低干扰。
- 默认落点应是已经进入 PR/MR 阶段的结果。
