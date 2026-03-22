---
name: practice-make-perfact
description: Codify a task-first workflow that turns real execution into reusable tools and skills. Use when asked to record process, standardize execution habits, or evolve ChatTool by adding general capabilities to src/ and task-specific guidance to skills/.
version: 0.1.0
---

# Practice Make Perfact

## Overview

Capture the working style that builds functionality first, then consolidates it into reusable tools and skills with post-task review.

## Workflow

1. Execute the task first  
   - Favor CLI interactions for read-only or data retrieval work.  
   - Avoid over-documenting before the task is done.

2. Classify the capability  
   - General/reusable: add to `src/` (tools, CLI, MCP as needed).  
   - Task-specific: add to `skills/<name>/` with `SKILL.md` and `SKILL.zh.md`.

3. Document the outcome  
   - Add or update a doc under `docs/` that explains the process.  
   - Update navigation (`mkdocs.yml`) if a new doc is added.

4. Normalize after completion  
   - Do a brief code review pass to align naming, structure, and docs.  
   - Ensure no unnecessary directories (keep paths flat where possible).

## Output Expectations

- Skills must include `SKILL.md` and `SKILL.zh.md`.  
- Treat “practice makes perfect” as a living workflow: apply it after each task.
