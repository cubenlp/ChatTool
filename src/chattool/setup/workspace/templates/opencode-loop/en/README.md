# Workspace

Human-AI collaboration workspace root.

This workspace uses `projects/` as the execution container for actual work. Workspace-level files help define protocol and context; project-level files drive execution.

This template enables OpenCode loop-aware mode:

- outer protocol files help the model understand document meaning, requirements, and rules
- inner `chatloop` only takes over after an explicit `/chatloop ...` trigger, then handles PRD-driven fresh-start continuation when the model is ready to stop

Also:

- source repositories stay under `core/` by default
- if a project needs a shorter repo path, create an on-demand symlink to `core/<repo-name>` inside that project instead of copying the repo
