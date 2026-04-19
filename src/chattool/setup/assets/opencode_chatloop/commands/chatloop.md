---
description: "Start a PRD-driven chat loop in the current directory"
---

# ChatLoop

Parse `$ARGUMENTS` as the initial user message.

Call the `chatloop` tool with:

- `message`: `$ARGUMENTS`

Requirements:

- the current directory or one of its parents must contain `PRD.md`
- if a message is provided, it is forwarded verbatim
- after that, ChatLoop restarts each iteration from scratch by asking the model to re-read `PRD.md`

Debugging:

- use `/chatloop-status` to inspect the resolved project root, state file, and log file
- state is written to `.opencode/chatloop.local.md` under the resolved project root
- logs are written to `.opencode/logs/<session-id>.log` under the resolved project root

Completion rule:

- if the PRD is satisfied, the model must output `<complete>DONE</complete>`
