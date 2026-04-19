# Workspace

Human-AI collaboration workspace root.

This workspace uses `projects/` as the execution container for actual work. Workspace-level files help define protocol and context; project-level files drive execution.

Conventions:

- source repositories stay under `core/` by default
- `projects/` only keeps the protocol files, drafts, and references needed for the current work
- if a project needs a shorter repo path, create an on-demand symlink to `core/<repo-name>` inside that project instead of copying the repo
