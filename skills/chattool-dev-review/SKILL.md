---
name: chattool-dev-review
description: Review a ChatTool feature after implementation. Use when asked to do a post-change audit focused on lazy import, missing-arg interactive behavior, unified utils/tui prompts, and whether docs/tests/changelog were updated with the feature.
version: 0.2.1
---

# ChatTool Dev Review

Use this skill after a new ChatTool feature or CLI change is implemented.

Default goal: review the feature change, not the whole repository, unless the user explicitly asks for a broader audit.

Boundary: this skill stops at development review. Merge timing, release prep, tag creation, `Publish Package`, PyPI verification, and `release.log` belong to `$chattool-release`.

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
   - New CLI prompts should use [src/chattool/interaction](src/chattool/interaction).
   - Avoid introducing fresh `click.prompt` / `click.confirm` flows for new interactive commands unless there is a strong reason and the behavior is documented.
   - Sensitive values must stay masked in prompts and summaries.

4. Docs and tests moved with the feature
   - Update the relevant docs under [docs](docs).
   - Update [README.md](README.md) when the feature is user-facing.
   - Update [CHANGELOG.md](CHANGELOG.md).
   - For CLI changes, update the matching doc-first case under [cli-tests](cli-tests) and add/adjust the `.py` test when needed.
   - If the PR is meant to ship as a specific package release, the intended `__version__` / changelog updates should already be in the diff before merge; do not defer version bumps to the post-merge tag step.

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

## Useful Commands

```bash
git diff --stat
git diff --name-only
rg -n "click\\.prompt|click\\.confirm|--interactive|--no-interactive|-i/-I|resolve_interactive_mode|ask_text|ask_confirm|ask_select|ask_path" src docs tests cli-tests
rg -n "lazy import|src/chattool/interaction|interactive" docs/development-guide docs README.md
```

## Output Rules

- Use a code review mindset.
- Findings come first, ordered by severity.
- Include file references and explain the concrete user or maintenance risk.
- Keep the summary brief after the findings.
- If no issues are found, say that explicitly and mention any residual testing gaps.
