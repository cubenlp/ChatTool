# Workspace Agents

`AGENTS.md` is the entry guide when a model enters this workspace.

## Core Principles

- Workspace-level files are for project authoring and guidance; actual execution should happen inside the target project directory.
- Use `projects/` as the top-level container for all active work.
- Default to a single-task project. Upgrade to a multi-task project only when the work clearly needs multiple coordinated tasks.
- Review is triggered by loop when the model is ready to stop; finish the work end-to-end first, then report once.
- For development tasks, each stage must pass its tests and update the docs before moving on; `review.md` defines validation and acceptance artifacts.

See `projects/README.md` for concrete project structures and naming rules.

## Architecture

```text
Workspace/
  README.md
  MEMORY.md
  TODO.md
  projects/
  docs/
  core/
  skills/
  public/
```

This outer workspace keeps collaboration artifacts outside the core repositories.

## Current Options

- Enabled options: `{{ENABLED_OPTIONS}}`
- Source repositories go under `core/`
- Durable notes live under `docs/`
- Imported shared skills go under `skills/`
- Public publish output goes under `public/`

## Workflow

1. Read `MEMORY.md` before starting work.
2. Identify the repo to change under `core/` and the target project under `projects/`.
3. Generate or refine project protocol files before starting execution.
4. Keep drafts and local references inside the current project rather than workspace-global buckets.
5. Let review files define validation and acceptance artifacts.
6. At the end, finish the report and update `MEMORY.md` if durable context changed.

## Write Rules

| Situation | Write To |
|-----------|----------|
| Single-task project work | `projects/MM-DD-<task-name>/` |
| Multi-task project root | `projects/MM-DD-<project-name>/` |
| Subtask work | `projects/MM-DD-<project-name>/tasks/<task-name>/` |
| Repositories to change | `core/<repo-name>/` |
| Durable context snapshots | `docs/memory/YYYY-MM-DD-status.md` |
| Tool notes | `docs/tools/<toolname>.md` |
| Reusable skills / practice | `docs/skills/` |

## Conventions

- Stay within the current task boundary unless the task is explicitly expanded.
- State uncertainty explicitly instead of silently assuming.
