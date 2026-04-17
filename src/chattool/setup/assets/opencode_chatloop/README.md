# ChatLoop Assets

This directory stores the local OpenCode `chatloop` plugin and slash commands that can be installed by ChatTool setup flows.

Current commands:

- `/chatloop`
- `/chatloop-help`
- `/chatloop-stop`

Current model:

- PRD-driven mode: user message goes through verbatim as the initial instruction, then every idle checkpoint triggers a fresh-start prompt that asks the model to re-read `PRD.md` and optional `memory.md` / `progress.md`
- completion is signaled by `<complete>DONE</complete>`
- logs are written to `.opencode/logs/<session-id>.log`
