---
description: "Start a PRD-driven chat loop in the current directory"
---

# ChatLoop

Parse `$ARGUMENTS` as the initial user message.

Call the `chatloop` tool with:

- `message`: `$ARGUMENTS`

Requirements:

- the current directory or one of its parents must contain `PRD.md`
- if a message is provided, it is preserved as the original task, but startup still injects the full PRD contract, project path, and `PRD.md` path
- every iteration must include `## Completed`, `## Next Steps`, and either `STATUS: IN_PROGRESS` or `STATUS: COMPLETE`
- after each idle checkpoint, ChatLoop restarts from a PRD-aware continuation prompt instead of relying on raw conversation context

Debugging:

- use `/chatloop-status` to inspect the resolved project root, state file, and events file
- state is written to `.opencode/chatloop.local.md` under the resolved project root
- event records are appended to `.opencode/chatloop.events.log` under the resolved project root

Completion rule:

- bootstrap iteration is never allowed to complete; the first response must stay `STATUS: IN_PROGRESS` and must not emit `<complete>DONE</complete>`
- if the PRD is satisfied, the model must output both `STATUS: COMPLETE` and `<complete>DONE</complete>`
- if unchecked `- [ ]` items remain in `## Next Steps`, ChatLoop will reject completion and continue looping
