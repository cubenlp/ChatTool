# Practice CLI Reference

This file is the quick index for the post-task normalization phase.

Use it when a task already works and you need to decide whether the result should stay as scratch work or be promoted into a real CLI / doc / skill asset.

## Core Rule

- If you had to write a one-off script to inspect, transform, send, or validate something twice, stop and check whether ChatTool should expose that capability as a CLI command.
- Prefer repository CLI over ad hoc SDK snippets when the action is user-facing, repeatable, or likely to appear in future tasks.

## Where To Look First

### Environment and config

- `chatenv init|cat|set|save|use`
- Docs: `docs/configuration.md`

### GitHub / delivery

- `chattool gh ...`
- Skill: `skills/chattool-gh/`

### Feishu / messaging / docs

- `chattool lark --help`
- `chattool lark doc --help`
- `lark-cli --help`
- Docs: `docs/tools/lark/index.md`
- Blog guide: `docs/blog/agent-cli/lark-cli-guide.md`
- Skill pointer: `skills/feishu/SKILL.md`

### Setup / local tooling

- `chattool setup ...`
- Docs: `docs/development-guide/`

### Skills

- `chattool skill ...`
- Repo skills: `skills/<name>/`

## Extraction Heuristics

When you finish a task, ask these in order:

1. Can the result become a stable CLI command under `src/chattool/.../cli.py`?
2. If not CLI, should it become a reusable Python helper under `src/`?
3. If task-specific, should it become a skill note or reference file under `skills/<name>/`?
4. Does the new behavior require:
   - `tests/cli-tests/*.md`
   - `docs/tools/<name>/index.md`
   - `README.md`
   - `CHANGELOG.md`

## Current High-Value CLI Surfaces

- `chattool lark`
- `chattool gh`
- `chattool setup`
- `chattool skill`
- `chattool pypi`
- `chattool dns`

## Expected Outcome

This reference should make the post-task decision simple:

- keep scratch outside the repo
- promote repeatable capability into CLI
- document the new stable surface immediately
