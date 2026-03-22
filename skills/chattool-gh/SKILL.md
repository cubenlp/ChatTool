---
name: chattool-gh
description: Use ChatTool GitHub CLI helpers (chattool gh) to create, update, list, and manage PRs. Use when tasks require opening PRs, updating PR metadata, or interacting with GitHub via ChatTool CLI.
version: 0.1.0
---

# ChatTool GitHub Helpers

## Overview

Use `chattool gh` for GitHub pull request workflows with correct body formatting.

## Prerequisites

Initialize GitHub credentials so `chattool gh` can read them:
```
chattool env init -t gh
```

## Create PR (Preferred)

Use a body file to avoid newline escaping:
```
cat > /tmp/pr_body.md <<'EOF'
## Summary
- point 1
- point 2

## Notes
- note 1
EOF

chattool gh pr-create \
  --repo owner/repo \
  --base master \
  --head your-branch \
  --title "feat: add xyz" \
  --body-file /tmp/pr_body.md
```

## Update PR Body

```
chattool gh pr-update \
  --repo owner/repo \
  --number 123 \
  --body-file /tmp/pr_body.md
```

## Listing / Viewing

```
chattool gh pr-list --repo owner/repo
chattool gh pr-view --repo owner/repo --number 123
```

## Notes

- Prefer `--body-file` to ensure Markdown renders correctly.
- Keep PR bodies short and structured (Summary, Notes).
