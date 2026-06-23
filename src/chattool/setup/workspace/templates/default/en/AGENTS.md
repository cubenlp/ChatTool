# Workspace Agents

`AGENTS.md` is the entry guide when a model enters this workspace.

## Core Principles

- Keep only a small set of control files at workspace root; actual execution should happen inside the target project directory.
- Keep all active work under `projects/`; archive inactive projects into `archive/YYYY-MM-DD/`.
- Project structure should stay minimal by default, while naming still allows more flexible grouping.
- `PRD.md` records stable requirements, scope, constraints, and completion criteria; progress details belong in `progress.md`.
- `progress.md` is the continuity log for each task. Update it after each substantive action.
- Archiving should not be decided by scripts alone. Scripts can collect candidates and validate rules, but the final archive index should be reviewed and written into `archive/index.md` by the model.
- If requirements are unclear, ask follow-up questions before execution.

See `projects/README.md` for concrete project structures and naming rules.

## Architecture

```text
Workspace/
  AGENTS.md
  TODO.md
  ARCHIVE.md
  .trash/
  projects/
  archive/
    index.md
    YYYY-MM-DD/
  core/
  scripts/
  skills/
  public/
```

This workspace is an outer collaboration scaffold around source repositories.

## Current Options

- Enabled options: `archive/`, `ARCHIVE.md`, `archive/index.md`
- Source repositories go under `core/`
- Workspace maintenance scripts go under `scripts/`
- The workspace root keeps a `.trash/` directory; prefer moving files there before deleting them directly
- Imported shared skills go under `skills/`
- Public publish output goes under `public/`
- Archived projects go under `archive/YYYY-MM-DD/`

## Workflow

1. Read root `AGENTS.md`, then enter the target project.
2. Identify the repo to change under `core/` and the target project under `projects/`.
3. Create or refine `PRD.md` before execution.
4. Update the current project's `progress.md` after each substantive action.
5. Keep drafts, experiments, and local references inside the current project and place them into the matching subdirectories.
6. Do not write debug temp files into `/tmp`; use the current project's `playground/`.
7. Keep the project root minimal: control files at the root, reports under `reports/`, scripts under `scripts/`.
8. If you use `projects/<topic>/<name>/`, keep `projects/<topic>/` as an index layer with only `README.md`, `.trash/`, and child project directories.
9. Use `MM-DD-...` for new execution tasks by default; only clearly long-lived stable subprojects should omit the date prefix.
10. Prefer `.trash/` at both workspace and project level; move files there before irreversible deletion.
11. If a project needs a shorter repo path, create an on-demand symlink to `core/<repo-name>` instead of copying the repository.
12. Finish with a report; if archiving happens, update `archive/index.md`.
13. Follow an archive flow of “script candidate collection + model review + `archive/index.md` update”; the procedure lives in root `ARCHIVE.md`.

## Write Rules

| Situation | Write To |
|-----------|----------|
| Any active work unit | `projects/<name>/` or `projects/<topic>/<name>/` |
| Short-term project | Prefer `MM-DD-<project-name>` |
| Long-lived project | Use a stable name without a date prefix |
| Inactive old project | `archive/YYYY-MM-DD/<project-name>/` |
| Archive procedure guide | `ARCHIVE.md` |
| Archived content index | `archive/index.md` |
| Repositories to change | `core/<repo-name>/` |
| Workspace maintenance scripts | `scripts/<name>.py` |

## Conventions

- Stay within the current task boundary unless the task is explicitly expanded.
- State uncertainty explicitly instead of silently assuming.
- Do not scatter standalone scripts or temp files at the workspace root; place durable scripts under `scripts/`.
