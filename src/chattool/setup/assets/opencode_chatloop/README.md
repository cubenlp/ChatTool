# ChatLoop Assets

This directory stores the local OpenCode `chatloop` plugin and slash commands that can be installed by ChatTool setup flows.

Current commands:

- `/chatloop`
- `/chatloop-status`
- `/chatloop-help`
- `/chatloop-stop`

Current model:

- PRD-driven mode: startup and every idle checkpoint both inject a strong PRD contract that includes the project path, required `PRD.md` path, optional `memory.md` / `progress.md` paths, and structured progress rules
- project root is resolved from the current directory upward until a `PRD.md` is found, so `/chatloop` can start from any project subdirectory
- every iteration must emit `## Completed`, `## Next Steps`, and `STATUS: IN_PROGRESS` or `STATUS: COMPLETE`
- the bootstrap iteration is never allowed to finish; completion is only checked from the first continuation onward
- completion requires both `STATUS: COMPLETE` and `<complete>DONE</complete>`, and is rejected if unchecked next steps remain
- state is written to `.opencode/chatloop.local.md` under the resolved project root
- event records are appended to `.opencode/chatloop.events.log` under the resolved project root
