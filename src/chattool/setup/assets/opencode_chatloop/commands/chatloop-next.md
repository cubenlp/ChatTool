---
description: "Prepare the project for the next chatloop task"
---

# ChatLoop Next

Use this command when the current task is effectively complete and you want to prepare the same project for discussing the next requirement.

Instructions for the model:

1. Review the current project state before making changes:
   - `PRD.md`
   - `memory.md`
   - `progress.md`
   - recent outputs and any files created for the current task
2. Package the current task's durable outputs into the project's `reference/` subdirectory.
   - prefer creating or updating a clearly named markdown summary inside `reference/`
   - do not move or delete source files unless the user explicitly asked for cleanup
3. Update `memory.md` so the next discussion has the right local context:
   - what was completed
   - where the key outputs now live
   - what the next discussion should know before changing direction
4. Update `progress.md` with a concise handoff note for the completed task.
5. Initialize the next-task discussion entrypoint by rewriting or preparing `PRD.md` for the upcoming requirement:
   - keep it minimal
   - preserve only durable context that still matters
   - if the next requirement is still ambiguous, leave a short scaffold with `## 待处理问题` / `## Open Questions`
6. When finished, summarize:
   - what was archived into `reference/`
   - what changed in `memory.md`
   - how `PRD.md` is now prepared for the next discussion

Important constraints:

- this command is for handoff and preparation, not for continuing the current implementation loop
- prefer small, explicit documentation updates over broad file churn
- keep the project reusable for the next requirement discussion
