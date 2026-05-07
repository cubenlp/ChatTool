---
name: chattool-gh
description: Use ChatTool GitHub CLI helpers (`chattool gh`) for PR creation, updates, CI checks, workflow run inspection, and GitHub credential setup through chatenv.
version: 0.4.1
---

# ChatTool GitHub Helpers

Use `chattool gh` for GitHub pull request workflows, CI inspection, and PR body formatting.

## Credentials

Store the GitHub token in typed env:

```bash
chatenv init -t gh
chatenv cat -t gh
```

Recommended key: `GITHUB_ACCESS_TOKEN`.

## Create PR

Prefer a body file so Markdown renders correctly:

```bash
cat > /tmp/pr_body.md <<'EOF'
## Summary
- point 1
- point 2

## Testing
- command 1
- command 2
EOF

chattool gh pr create --repo owner/repo --base master --head your-branch --title "feat: add xyz" --body-file /tmp/pr_body.md
```

## Update PR

Update the PR body whenever scope changes:

```bash
chattool gh pr edit --repo owner/repo --number 123 --body-file /tmp/pr_body.md
```

You can also update title, state, or base branch:

```bash
chattool gh pr edit --repo owner/repo --number 123 --title "feat: refine xyz" --state open
```

## Inspect PRs And CI

```bash
chattool gh pr list --repo owner/repo
chattool gh pr view --repo owner/repo --number 123
chattool gh pr checks --repo owner/repo --number 123
chattool gh pr checks --repo owner/repo --number 123 --wait
chattool gh pr checks --repo owner/repo --number 123 --wait --interval 10 --timeout 600
chattool gh run view --repo owner/repo --run-id 23494900414
chattool gh run logs --repo owner/repo --job-id 68373094563
```

After pushing PR updates, prefer:

```bash
chattool gh pr checks --repo owner/repo --number 123 --wait
```

Use one-shot `pr checks` only when you explicitly want a snapshot.

For machine-readable output:

```bash
chattool gh pr checks --repo owner/repo --number 123 --json-output
```

## Comment And Merge

```bash
chattool gh pr comment --repo owner/repo --number 123 --body "Looks good"
chattool gh pr merge --repo owner/repo --number 123 --method squash
chattool gh pr merge --repo owner/repo --number 123 --method squash --check
```

## Notes

- Prefer `--body-file` for PR create/edit.
- Keep PR bodies short and structured with `Summary` and `Testing`.
- Use `pr checks` before inspecting individual workflow runs.
- If CI is red, drill down with `run view` and `run logs` instead of guessing from the web UI.
- Before requesting review, update from the target main branch and resolve conflicts locally.
