---
name: chattool-gh
description: Use ChatTool GitHub CLI helpers (chattool gh) to create, update, inspect, and maintain PRs, including CI status checks. Use when tasks require opening PRs, updating PR metadata, checking workflow status, or interacting with GitHub via ChatTool CLI.
version: 0.4.0
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

chattool gh pr create \
  --repo owner/repo \
  --base master \
  --head your-branch \
  --title "feat: add xyz" \
  --body-file /tmp/pr_body.md
```

## Update PR Title / Body

Update the PR body whenever the scope changes:

```
chattool gh pr edit \
  --repo owner/repo \
  --number 123 \
  --body-file /tmp/pr_body.md
```

You can also update title, state, or base branch:

```
chattool gh pr edit \
  --repo owner/repo \
  --number 123 \
  --title "feat: refine xyz" \
  --state open
```

## Listing / Viewing / Checking

```
chattool gh pr list --repo owner/repo
chattool gh pr view --repo owner/repo --number 123
chattool gh pr checks --repo owner/repo --number 123
chattool gh pr checks --repo owner/repo --number 123 --wait
chattool gh pr checks --repo owner/repo --number 123 --wait --interval 10 --timeout 600
chattool gh run view --repo owner/repo --run-id 23494900414
chattool gh run logs --repo owner/repo --job-id 68373094563
```

Use `pr checks` after pushing or when CI looks wrong. It summarizes:
- combined status
- check runs
- workflow runs

If you pass `--wait`, it will keep polling until checks and workflow runs finish:
- default: no timeout, wait until completion
- `--interval <seconds>`: control polling interval
- `--timeout <seconds>`: fail only when you explicitly want a timeout

Recommended default for active PR work:

```bash
chattool gh pr checks --repo owner/repo --number 123 --wait
```

Use plain `pr checks` only when you explicitly want a one-shot snapshot.

For machine-readable output:

```
chattool gh pr checks --repo owner/repo --number 123 --json-output
```

## Comment / Merge

```
chattool gh pr comment --repo owner/repo --number 123 --body "Looks good"
chattool gh pr merge --repo owner/repo --number 123 --method squash
chattool gh pr merge --repo owner/repo --number 123 --method squash --check
```

## Notes

- Prefer `--body-file` to ensure Markdown renders correctly.
- Keep PR bodies short and structured (`Summary`, `Testing`).
- Prefer `pr checks` over manually browsing GitHub Actions when the task is to inspect PR CI state.
- When CI is still running, prefer `pr checks --wait` instead of manually re-running status commands.
- Before asking for review / MR, update from the target main branch first and resolve conflicts locally, so reviewers do not take avoidable merge debt.
- If CI is red, use `pr checks` first, then `run view` / `run logs` to drill down instead of guessing from the web UI.
- When extending `chattool gh`, check the official GitHub REST docs and PyGithub references in `docs/client.md`.
