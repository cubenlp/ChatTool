---
name: chattool-gh
description: Use ChatTool GitHub CLI helpers (chattool gh) to create, update, inspect, and maintain PRs, including CI status checks. Use when tasks require opening PRs, updating PR metadata, checking workflow status, or interacting with GitHub via ChatTool CLI.
version: 0.2.0
---

# ChatTool GitHub Helpers

## Overview

Use `chattool gh` for GitHub pull request workflows, CI inspection, and correct PR body formatting.

## Prerequisites

Initialize GitHub credentials so `chattool gh` can read them:
```
chatenv init -t gh
chatenv cat -t gh
```

Recommended config keys:
- `GITHUB_ACCESS_TOKEN`
- `GITHUB_DEFAULT_REPO`

## Create PR (Preferred)

Use a body file to avoid newline escaping:
```
cat > /tmp/pr_body.md <<'EOF'
## Summary
- point 1
- point 2

## Testing
- command 1
- command 2
EOF

chattool gh pr-create \
  --repo owner/repo \
  --base master \
  --head your-branch \
  --title "feat: add xyz" \
  --body-file /tmp/pr_body.md
```

## Update PR Title / Body

Update the PR body whenever the scope changes:

```
chattool gh pr-update \
  --repo owner/repo \
  --number 123 \
  --body-file /tmp/pr_body.md
```

You can also update title, state, or base branch:

```
chattool gh pr-update \
  --repo owner/repo \
  --number 123 \
  --title "feat: refine xyz" \
  --state open
```

## Listing / Viewing / Checking

```
chattool gh pr-list --repo owner/repo
chattool gh pr-view --repo owner/repo --number 123
chattool gh pr-check --repo owner/repo --number 123
```

Use `pr-check` after pushing or when CI looks wrong. It summarizes:
- combined status
- check runs
- workflow runs

For machine-readable output:

```
chattool gh pr-check --repo owner/repo --number 123 --json-output
```

## Comment / Merge

```
chattool gh pr-comment --repo owner/repo --number 123 --body "Looks good"
chattool gh pr-merge --repo owner/repo --number 123 --method squash --confirm
```

## Notes

- Prefer `--body-file` to ensure Markdown renders correctly.
- Keep PR bodies short and structured (`Summary`, `Testing`).
- Prefer `pr-check` over manually browsing GitHub Actions when the task is to inspect PR CI state.
- When extending `chattool gh`, check the official GitHub REST docs and PyGithub references in `docs/client.md`.
