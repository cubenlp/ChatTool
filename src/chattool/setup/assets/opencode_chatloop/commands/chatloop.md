---
description: "Start single-task chat loop in the current TASK.md project"
---

# ChatLoop

Parse `$ARGUMENTS` as the user message.

Call the `chatloop` tool with:

- `message`: `$ARGUMENTS`

This command is only for single-task projects.

- The current directory must contain `TASK.md`
- Your message is forwarded verbatim to the model

After the tool confirms the loop is active, continue working inside the current task project.

Execution rule:

- your message starts the normal work phase
- when the model is ready to stop, the plugin reads `review.md` to validate whether it should continue or exit

Do not ask the user to restate the task if the project files already define it.
