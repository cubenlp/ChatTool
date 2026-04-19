# Workspace Agents

`AGENTS.md` is the entry guide when a model enters this workspace.

## Core Principles

- Workspace-level files are for project authoring and guidance; actual execution should happen inside the target project directory.
- Use `projects/` as the top-level container for all active work.
- This workspace is loop-aware for OpenCode: outer protocol files explain the rules, while inner `chatloop` only runs after an explicit `/chatloop ...` trigger.
- Focus early conversation on refining `PRD.md`; execution should follow `PRD.md` as the primary entry file.
- If a project needs a shorter repo path, create an on-demand symlink to `core/<repo-name>` instead of copying the repository.
- Promote reusable references across projects into `reference/`.
- Promote long-lived maintenance conventions into `docs/themes/`.

See `projects/README.md` for concrete project structures and naming rules.

## Architecture

```text
Workspace/
  README.md
  MEMORY.md
  TODO.md
  projects/
  reference/
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
- Cross-project reusable references go under `reference/`
- Theme-organized maintenance rules go under `docs/themes/`

## Workflow

1. Read `MEMORY.md` before starting work.
2. Identify the repo to change under `core/` and the target project under `projects/`.
3. Generate or refine project protocol files before starting execution.
4. Keep drafts and local references inside the current project rather than workspace-global buckets.
5. Only after `/chatloop ...` is triggered should ChatLoop take over idle-time fresh-start continuation from `PRD.md`.
6. At the end, finish the report and update `MEMORY.md` if durable context changed.
7. If some material is clearly reusable across projects, promote it into workspace-level `reference/` or `docs/themes/` instead of leaving it in one project.

## Write Rules

| Situation | Write To |
|-----------|----------|
| Any active work unit | `projects/MM-DD-<project-name>/` |
| Cross-project reusable reference | `reference/` |
| Repositories to change | `core/<repo-name>/` |
| Durable context snapshots | `docs/memory/YYYY-MM-DD-status.md` |
| Tool notes | `docs/tools/<toolname>.md` |
| Reusable skills / practice | `docs/skills/` |
| Theme maintenance rules | `docs/themes/` |

## Conventions

- Stay within the current task boundary unless the task is explicitly expanded.
- State uncertainty explicitly instead of silently assuming.
