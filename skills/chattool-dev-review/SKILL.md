---
name: chattool-dev-review
description: Review a ChatTool feature after implementation. Use when asked to do a post-change audit focused on lazy import, missing-arg interactive behavior, unified utils/tui prompts, and whether docs/tests/changelog were updated with the feature.
version: 0.1.0
---

# ChatTool Dev Review

Use this skill after a new ChatTool feature or CLI change is implemented.

Default goal: review the feature change, not the whole repository, unless the user explicitly asks for a broader audit.

## What To Check

1. Minimum import / lazy import
   - Entry wiring should stay lazy at [src/chattool/client/main.py](src/chattool/client/main.py).
   - CLI modules should avoid top-level imports that pull in heavy implementation code when a function-level import would work.
   - Prefer implementation imports inside command functions when they are only needed on execution.

2. Missing args -> interactive behavior
   - If required inputs can be recovered interactively, missing args should auto-enter interactive mode.
   - `-i` should force the current command's interactive flow.
   - `-I` should fully disable prompting and fail fast when required inputs are missing.
   - Defaults shown in prompts must match the actual execution defaults.

3. Unified interactive style
   - New CLI prompts should use [src/chattool/utils/tui.py](src/chattool/utils/tui.py).
   - Avoid introducing fresh `click.prompt` / `click.confirm` flows for new interactive commands unless there is a strong reason and the behavior is documented.
   - Sensitive values must stay masked in prompts and summaries.

4. Docs and tests moved with the feature
   - Update the relevant docs under [docs](docs).
   - Update [README.md](README.md) when the feature is user-facing.
   - Update [CHANGELOG.md](CHANGELOG.md).
   - For CLI changes, update the matching doc-first case under [cli-tests](cli-tests) and add/adjust the `.py` test when needed.

5. Branch is rebased or merged with the latest mainline before MR/PR
   - Before the final MR/PR pass, update from the latest `master` branch.
   - Prefer merging or rebasing `origin/master` into the working branch before submission, then resolve conflicts locally.
   - Treat “not synced with latest master” as a review issue because it hides integration conflicts until review or merge time.

## Review Workflow

1. Scope the review.
   - Prefer the current diff: `git diff --stat`, `git diff --name-only`, `git diff --cached --name-only`.
   - If the user names files or a feature, focus there first.
   - Only do a repo-wide audit when explicitly requested.

2. Inspect CLI entry and changed command files.
   - Look for new top-level imports in `cli.py` / `main.py`.
   - Look for `click.prompt` / `click.confirm` added in new interactive flows.
   - Look for `--interactive/--no-interactive`, `-i/-I`, and missing-arg handling.

3. Check docs and tests next to the change.
   - Search for the command name in `docs/`, `README.md`, `CHANGELOG.md`, and `cli-tests/`.
   - Treat undocumented new flags, env vars, or behavior changes as findings.

4. Validate the most relevant path.
   - Run the smallest useful test or CLI invocation for the changed feature.
   - If you cannot validate, say so explicitly.

5. Before final MR/PR, sync mainline and recheck.
   - Run `git fetch origin` and bring `origin/master` into the current branch.
   - Resolve conflicts before final review output or PR update.
   - Re-run the smallest relevant verification after conflict resolution when the merge changes the affected area.

## Useful Commands

```bash
git diff --stat
git diff --name-only
git fetch origin
git merge origin/master
rg -n "click\\.prompt|click\\.confirm|--interactive|--no-interactive|-i/-I|resolve_interactive_mode|ask_text|ask_confirm|ask_select|ask_path" src docs tests cli-tests
rg -n "lazy import|utils/tui.py|interactive" docs/development-guide docs README.md
```

## Output Rules

- Use a code review mindset.
- Findings come first, ordered by severity.
- Include file references and explain the concrete user or maintenance risk.
- Keep the summary brief after the findings.
- If no issues are found, say that explicitly and mention any residual testing gaps.
