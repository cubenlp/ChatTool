---
name: practice-make-perfact
description: Post-task normalization workflow for ChatTool development: update project PRD/progress, extract durable artifacts, check existing CLI surfaces, run dev review, and finish docs/tests/changelog/PR work.
version: 0.5.0
---

# Practice Make Perfact

Use this skill after a ChatTool feature, fix, refactor, CLI change, skill update, or documentation-backed behavior change is basically working.

This is a post-task normalization workflow, not a pre-task exploration guide.

## Workflow

1. Review the actual work product
   - Read the current diff, changed files, and any generated outputs.
   - Separate durable repository artifacts from scratch notes or temporary experiments.
   - Keep temporary exploration outside the repository unless it must become maintained documentation.

2. Update project-local records first
   - If the task lives under `projects/<date>-<name>/`, update that project's `PRD.md`, `progress.md`, and `memory.md` before promoting durable artifacts.
   - Do not promote raw one-off research into workspace root references.
   - Move only normalized, durable outputs into ChatTool `src/`, `docs/`, `skills/`, or `tests/`.

3. Check existing CLI surfaces before adding scripts
   - Look at `references/cli-reference.md` first.
   - Prefer existing `chatpypi`, `chattool skill`, `chatenv`, `chatgh`, and `chattool dns` commands over ad hoc scripts.
   - Add a script only when the action is repeatable, fragile, and not already covered by a CLI.

4. Normalize ChatArch boundaries
   - ChatTool commands should use `chattool.interaction` adapters when they need ChatTool policy or test patch points.
   - Standalone ChatArch packages should use external `chatstyle` and `chatenv` directly.
   - New env/profile schemas should be provider modules registered through `chatenv.configs`.

5. Normalize skills
   - Skill changes must keep `SKILL.md` and `SKILL.zh.md` aligned.
   - If a skill has `agents/openai.yaml`, update the metadata when behavior or trigger scope changes.
   - New skills should normally include English and Chinese instructions plus agents metadata.
   - Run a stale-command grep after skill edits.

6. Run the post-task review
   - Review the current diff, not the whole repo by default.
   - Check lazy imports, interactive `-i/-I` behavior, ChatStyle/ChatEnv boundaries, docs, tests, README, and changelog.
   - Use `$chattool-dev-review` unless the user explicitly says not to.

7. Carry the work to PR/MR stage
   - Commit and push the branch.
   - Use `chatgh` for GitHub read/check operations such as `pr view`, `pr checks`, `run view`, and `run logs`.
   - For PR creation or body updates, use the project's current GitHub workflow or API path until ChatGH exposes public write commands.
   - When CI status is part of the handoff, query `chatgh pr checks <pr> --repo owner/repo` after GitHub checks reach a terminal state.

8. Hand off real release work
   - Tags, package publishing, and PyPI verification belong to `$chattool-release` after merge.
   - Do not tag from an unmerged PR head.
   - Release version bumps happen before PR/MR, not after merge.
   - If PyPI already has the target version, create a new PR with a new version.

## Required Outputs

- The repository diff is normalized into maintained locations.
- Project-local `PRD.md` / `progress.md` / `memory.md` are updated when present.
- Skills include matching English and Chinese files.
- Docs/tests/changelog updates accompany behavior changes.
- The task reaches PR/MR stage unless the user explicitly asks to stop earlier.
