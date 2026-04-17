# ChatLoop Assets

This directory stores the local OpenCode `chatloop` plugin and slash commands that can be installed by ChatTool setup flows.

Current commands:

- `/chatloop`
- `/chatloop-project`
- `/chatloop-help`
- `/chatloop-stop`

Current model:

- single-task mode: user message goes through verbatim, idle triggers review, review decides continue or exit
- project mode: user message starts the first selected task directly, task review returns to project review, project review decides next task or completion
