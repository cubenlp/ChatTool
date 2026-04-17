# Workspace

Human-AI collaboration workspace root.

This workspace uses `projects/` as the execution container for actual work. Workspace-level files help define protocol and context; project-level files drive execution.

This template enables OpenCode loop-aware mode:

- outer protocol files help the model understand document meaning, requirements, and rules
- inner `chatloop` / `chatloop-project` only handle review-time continuation when the model is ready to stop
