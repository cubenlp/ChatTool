---
description: "Start a PRD-driven chat loop in the current directory"
---

# ChatLoop

Parse `$ARGUMENTS` as the initial user message.

Call the `chatloop` tool with:

- `message`: `$ARGUMENTS`

Requirements:

- the current directory must contain `PRD.md`
- if a message is provided, it is forwarded verbatim
- after that, ChatLoop restarts each iteration from scratch by asking the model to re-read `PRD.md`

Completion rule:

- if the PRD is satisfied, the model must output `<complete>DONE</complete>`
