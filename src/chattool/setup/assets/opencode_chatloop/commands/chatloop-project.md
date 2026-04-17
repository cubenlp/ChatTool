---
description: "Start project-level chat loop in the current PROJECT.md project"
---

# ChatLoop Project

Parse `$ARGUMENTS` as the user message.

Call the `chatloop-project` tool with:

- `message`: `$ARGUMENTS`

This command is only for multi-task projects.

- The current directory must contain `PROJECT.md`
- Project-level rules determine the initial active task
- Your message is forwarded verbatim into that first task loop
- Project-level `review.md` is used when a task loop exits and the plugin needs to decide the next task or finish the project

Do not ask the user to restate the project if the current project files already define it.
