---
name: practice-make-perfact
description: Post-task normalization workflow for ChatTool development. Use after implementation to review the completed work, extract reusable pieces into the repo, check existing CLI surfaces before adding scripts, run $chattool-dev-review, and then drive docs/tests/changelog/PR updates through the project standards. If the task also includes merged-mainline release work, hand off to $chattool-release after PR/MR stage.
version: 0.4.1
---

# Practice Make Perfact

## Overview

This is the post-task normalization workflow for ChatTool repository tasks.

Use it after finishing a ChatTool feature, fix, refactor, CLI change, skill update, or documentation-backed behavior change.

Core idea: finish the task first, then explicitly enter a cleanup and extraction phase that turns useful outcomes into durable repository assets.

## Workflow

1. Enter only after the task basically works
   - Do not use this as a pre-task reminder or exploration guide.
   - Start once the implementation direction is already settled and the main task is materially complete.
   - Treat this as an explicit post-processing phase.

2. Review what was actually produced
   - Read the current diff, changed files, and any temporary outputs created during the task.
   - Separate durable outcomes from scratch artifacts.
   - Keep temporary exploration material outside the repository unless there is a clear reason to preserve it.

3. Extract reusable content into the right repository locations
   - Move general or reusable capability into `src/`.
   - Move task-specific guidance into `skills/<name>/`.
   - Promote only durable outputs into `docs/`, tests, or source files.
   - Normalize naming, placement, and file boundaries so the repository stays coherent.
   - Before keeping an ad hoc script, check whether an existing CLI already covers the action.
   - Use `references/cli-reference.md` as the first lookup index for this pass.

4. Run the mandatory post-task review
   - Review the actual diff, not the whole repo by default.
   - Check minimum import / lazy import.
   - Check missing-arg auto interactive behavior and `-i/-I`.
    - Check new prompts use `src/chattool/interaction/` where appropriate.
   - Check tests, docs, `README.md`, `CHANGELOG.md`, and `cli-tests` moved with the change.
   - Always call `$chattool-dev-review` for this pass unless the user explicitly asks not to.

5. Normalize deliverables
   - Add or update docs under `docs/`.
   - Update `README.md` for user-facing changes.
   - Update `CHANGELOG.md`.
   - If this work is intended to ship as a specific package release, bump `src/chattool/__init__.py` to the target version before PR/MR, not after merge.
   - If a skill is added or updated, maintain both `SKILL.md` and `SKILL.zh.md`.
   - Keep skill frontmatter aligned, including `version`.
   - Keep directory structure flat and intentional.
   - Only bring durable outputs back into the repository after they are normalized into the right docs, tests, or source locations.

6. Carry the task through PR/MR stage
   - Ensure the branch is committed and pushed.
   - Use `chattool gh` for GitHub PR operations.
   - Prefer `chattool gh pr create --body-file ...` to open the PR.
   - Update the PR body when the scope changes.
   - Continue until the work is in PR/MR stage, not just local commit stage.

7. Hand off real release work explicitly
   - If the task includes version tags, `Publish Package`, PyPI verification, or `release.log`, switch to `$chattool-release`.
   - Treat post-merge release work as a separate phase from development review.
   - Do not tag from an unmerged PR head just because the implementation is ready.
   - Do not treat “push the tag again” as a fix for a missed version bump. If PyPI already has that version, the next step is a new PR with a new version, not a reused tag.

8. Only stop early when explicitly asked
   - If the user wants analysis only, brainstorming only, or a partial checkpoint, respect that.
   - Otherwise, default to the full post-task cleanup -> review -> PR workflow.

## Output Expectations

- Skills must include `SKILL.md` and `SKILL.zh.md`.
- Treat this as a post-processing workflow, not an exploration workflow.
- It should help the model look back at completed work, extract the useful parts, and normalize them into the repository.
- It should explicitly chain into `$chattool-dev-review` to enforce development standards.
- If the user asks for a real release after merge, it should hand off that phase to `$chattool-release`.
- The expected resting point is usually an updated PR/MR, not just local edits.
- It should keep a small CLI reference surface so the model can quickly audit “what command already exists” before adding another temporary script.
