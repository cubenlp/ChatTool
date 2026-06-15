---
name: chattool-dev-review
description: Review ChatTool or ChatArch feature changes for lazy imports, interactive CLI behavior, chatstyle/chatenv boundaries, docs/tests/changelog updates, and release-boundary correctness.
version: 0.3.0
---

# ChatTool Dev Review

Use this skill after a ChatTool or ChatArch feature, CLI change, skill change, or scaffold update is implemented.

Default scope: review the current change, not the whole repository, unless the user explicitly asks for a broad audit.

Boundary: this skill stops at development review. Merge timing, tags, package publishing, and PyPI verification belong to `$chattool-release`.

## What To Check

1. Lazy import and command wiring
   - `src/chattool/client/main.py` should keep subcommands lazy.
   - CLI modules should avoid import-time loading of heavy implementation code.
   - Imports only needed for command execution should usually live inside command functions.

2. Interactive CLI behavior
   - Recoverable missing inputs should auto-enter interactive mode in a TTY.
   - `-i` should force the current command's prompt flow.
   - `-I` should disable prompts and fail fast when required inputs are missing.
   - Prompt defaults must match actual execution defaults.
   - Sensitive values must be masked in prompts and summaries.

3. ChatStyle boundary
   - External `chatstyle` is the canonical runtime for shared prompt, choice, render, mask, and schema behavior.
   - ChatTool commands should use `chattool.interaction` when they need ChatTool policy, usage text, warning filters, or existing mock patch points.
   - Standalone ChatArch packages should import `chatstyle` directly and must not depend on `chattool.interaction`.
   - Do not recreate a local style/runtime layer inside ChatTool.

4. ChatEnv boundary
   - `chatenv` is an independent CLI for typed env/profile operations.
   - ChatTool should expose concrete config schemas through `[project.entry-points."chatenv.configs"]`.
   - New business packages should register provider modules; they should not copy the env CLI or make `chatenv` hard-code business imports.
   - Examples should use `chatenv init -t <alias>` and `chatenv cat -t <alias>`, not a nested ChatTool env command.

5. PyPI scaffold correctness
   - `chattool pypi` examples must match the current command surface: `init/build/check/probe/upload`.
   - `chatarch` scaffold examples should include `chatstyle` and `chatenv` dependencies and current mkdocs/workflow options.
   - `chatpypi <name>` may be documented as a convenience wrapper for `chattool pypi init <name>`.

6. Docs, tests, and changelog
   - Update relevant docs under `docs/` when behavior changes.
   - Update `README.md` for user-facing behavior.
   - Update `CHANGELOG.md` for feature/fix/skill updates.
   - For CLI changes, keep doc-first cases under `tests/cli-tests/` or mock cases under `tests/mock-cli-tests/` aligned.
   - If a PR is intended for a specific release, the version/changelog changes should already be in the diff before merge.

## Review Workflow

1. Scope the review with `git diff --stat`, `git diff --name-only`, and user-provided context.
2. Inspect changed CLI entrypoints, command modules, skills, docs, and tests.
3. Search for stale command names or boundary violations.
4. Run the smallest useful validation command or test for the changed path.
5. Report findings first, ordered by severity, with file references and concrete risk.

## Useful Commands

```bash
git diff --stat
git diff --name-only
rg -n "click\.prompt|click\.confirm|--interactive|--no-interactive|-i/-I|resolve_interactive_mode|ask_text|ask_confirm|ask_select|ask_path" src docs tests skills
rg -n "pypi|cert|chatenv|chatstyle|chattool.interaction" skills docs tests README.md CHANGELOG.md
rg -n "chatstyle|chattool.interaction|chatenv.configs|BaseEnvConfig|EnvField" src docs tests skills pyproject.toml
```

## Output Rules

- Use a code review mindset.
- Findings come first, ordered by severity.
- Include file references and explain the concrete user or maintenance risk.
- Keep summaries brief and place them after findings.
- If no issues are found, say that explicitly and mention residual testing gaps.
