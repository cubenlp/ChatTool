---
name: practice-make-perfact
description: Default workflow for ChatTool development tasks. Use at the start of any ChatTool repo task with a light-touch reminder to stay task-first, then apply strict review, docs/tests/changelog sync, and chattool gh PR handling once implementation direction is clear.
version: 0.1.0
---

# Practice Make Perfact

## Overview

This is the default development workflow for ChatTool repository tasks.

Use it before working on a ChatTool feature, fix, refactor, CLI change, skill update, or documentation-backed behavior change.

Core idea: keep early exploration light, then switch to a strict normalization flow once the task direction is clear.

## Workflow

1. Start from the task, not from process polish
   - Read this skill first for ChatTool repo work.
   - Then switch attention to the concrete user task.
   - Prefer direct execution over early process discussion.
   - Favor existing `chattool` CLI commands for reproducible read or export steps.
   - Do not over-constrain early exploration, repo reading, or solution shaping.
   - At this stage, this skill should act as a gentle orientation only.
   - Use `playground/` as the default scratch area for temporary exploration artifacts.

2. Finish implementation before broad normalization
   - Make the feature, fix, or content change work first.
   - Keep general/reusable capability in `src/`.
   - Keep task-specific guidance in `skills/<name>/`.
   - Do not over-document unfinished work.

3. Turn strict only after the path is clear
   - Once implementation has started or the solution direction is settled, switch into the full normalization flow.
   - Before that point, avoid interrupting exploration with heavyweight process steps.

4. Run the mandatory post-task review
   - Review the actual diff, not the whole repo by default.
   - Check minimum import / lazy import.
   - Check missing-arg auto interactive behavior and `-i/-I`.
   - Check new prompts use `utils/tui.py` where appropriate.
   - Check tests, docs, `README.md`, `CHANGELOG.md`, and `cli-tests` moved with the change.
   - If relevant, use `$chattool-dev-review` for this pass.

5. Normalize deliverables
   - Add or update docs under `docs/`.
   - Update `README.md` for user-facing changes.
   - Update `CHANGELOG.md`.
   - If a skill is added or updated, maintain both `SKILL.md` and `SKILL.zh.md`.
   - Keep skill frontmatter aligned, including `version`.
   - Keep directory structure flat and intentional.
   - Move only durable outputs out of `playground/`; leave scratch exploration there.

6. Carry the task through PR/MR stage
   - Ensure the branch is committed and pushed.
   - Use `chattool gh` for GitHub PR operations.
   - Prefer `chattool gh pr-create --body-file ...` to open the PR.
   - Update the PR body when the scope changes.
   - Continue until the work is in PR/MR stage, not just local commit stage.

7. Only stop early when explicitly asked
   - If the user wants analysis only, brainstorming only, or a partial checkpoint, respect that.
   - Otherwise, default to the full task-first -> review -> PR workflow.

## Output Expectations

- Skills must include `SKILL.md` and `SKILL.zh.md`.
- Treat this as a living workflow for every ChatTool development task.
- Early exploration should feel minimally constrained.
- The expected resting point is usually an updated PR/MR, not just local edits.
