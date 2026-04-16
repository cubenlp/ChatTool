# Projects

This directory contains all active work. Each project should be self-contained enough that execution can happen mostly inside that project directory.

## When to create a new project

Create a new project when the work has its own goal, context, and deliverables. Examples:

- a research task
- a one-off implementation
- a bugfix stream
- a larger initiative that may later split into multiple tasks

## Naming

Use `MM-DD-<project-name>` for each project directory.

## Single-task project

Start with the simplest structure:

```text
MM-DD-<task-name>/
  TASK.md
  progress.md
  review.md
  memory.md
  playground/
  reference/
```

Use this for research, one-off development, focused cleanup, and other work that can stay inside one task boundary.

## Multi-task project

Upgrade to a multi-task project only when the work clearly needs multiple coordinated tasks:

```text
MM-DD-<project-name>/
  PROJECT.md
  progress.md
  review.md
  tasks/
    <task-name>/
      TASK.md
      progress.md
      review.md
      memory.md
      playground/
      reference/
```

Use this when task ordering, dependency management, or project-level review needs a project root.

## Subtask naming

Subtask directories inside a multi-task project do not need a date prefix.

You can organize them in two ways:

### 1. Ordered Tasks

If tasks have a clear execution order, encode that order directly in the task name:

```text
tasks/
  01-workspace-protocol/
  02-chatloop-plugin/
  03-install-chain/
```

In this mode, project-level dispatch follows the order.

### 2. Review-Directed Tasks

If dependencies are more complex, or priority must be decided dynamically, task names can stay free-form and project-level `review.md` selects the current active task:

```text
tasks/
  workspace-protocol/
  chatloop-plugin/
  install-chain/
```

Prefer the simpler mode by default:

- use numbered tasks when the order is clear
- use project-level `review.md` dispatch only when that order is not fixed

## File roles

- `TASK.md`: task goal, scope, acceptance
- `PROJECT.md`: project goal, boundaries, phases
- `progress.md`: current status, decisions, next step
- `review.md`: validation rules and required acceptance artifacts
- `memory.md`: local context, important files, working notes
- `playground/`: drafts, experiments, temporary outputs
- `reference/`: project-local references and samples

## Upgrade rule

Default to a single-task project. Only introduce `tasks/` when one task is no longer enough to describe and control the work clearly.
