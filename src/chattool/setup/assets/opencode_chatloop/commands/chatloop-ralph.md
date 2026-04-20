---
description: "Start a PRD-aware refresh loop"
---

# ChatLoop Ralph

Parse `$ARGUMENTS` as the original task.

Call the `chatloop-ralph` tool with:

- `message`: `$ARGUMENTS`

Requirements:

- the current directory itself must contain `PRD.md`
- startup creates a fresh session and switches the TUI to it
- each later continuation runs in another newly refreshed session
- rely on `PRD.md`, `memory.md`, `progress.md`, and structured progress instead of old chat history

Debugging:

- use `/chatloop-project` to inspect the resolved project root and file paths
- use `/chatloop-status` to inspect the current loop mode, state, and last lifecycle reason
- state is written to `.opencode/chatloop.local.md`
- event records are appended to `.opencode/chatloop.events.log`

Completion rule:

- bootstrap iteration is never allowed to complete
- only later iterations may finish with both `STATUS: COMPLETE` and `<complete>DONE</complete>`
