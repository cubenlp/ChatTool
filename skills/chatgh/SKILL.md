---
name: chatgh
description: Use the standalone ChatGH CLI (`chatgh`) for GitHub PR creation, updates, CI checks, workflow run inspection, and GitHub credential setup through chatenv.
version: 0.5.0
---

# ChatGH GitHub Helpers

Use `chatgh` for GitHub pull request workflows, CI inspection, and PR body formatting. Do not use the removed `chattool gh` entrypoint.

## Credentials

Store the GitHub token in typed env:

```bash
chatenv init -t gh
chatenv cat -t gh
```

Recommended key: `GITHUB_ACCESS_TOKEN`.

For repo-scoped Git HTTPS credentials, use:

```bash
chatgh set-token
```

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

chatgh pr-legacy create --repo owner/repo --base master --head your-branch --title "feat: add xyz" --body-file /tmp/pr_body.md
```

## Update PR

Update the PR body whenever scope changes:

```bash
chatgh pr-legacy edit --repo owner/repo --number 123 --body-file /tmp/pr_body.md
```

You can also update title, state, or base branch:

```bash
chatgh pr-legacy edit --repo owner/repo --number 123 --title "feat: refine xyz" --state open
```

## Inspect PRs And CI

Use the generated default `pr` commands where available:

```bash
chatgh pr list --repo owner/repo
chatgh pr view 123 --repo owner/repo
chatgh pr checks 123 --repo owner/repo
```

Use `pr-legacy` for the full hand-written feature set that has not migrated yet:

```bash
chatgh pr-legacy checks --repo owner/repo --number 123 --wait
chatgh pr-legacy checks --repo owner/repo --number 123 --wait --interval 10 --timeout 600
chatgh run view --repo owner/repo --run-id 23494900414
chatgh run logs --repo owner/repo --job-id 68373094563
```

After pushing PR updates, prefer:

```bash
chatgh pr-legacy checks --repo owner/repo --number 123 --wait
```

Use one-shot `pr checks` only when you explicitly want a snapshot.

For machine-readable output:

```bash
chatgh pr checks 123 --repo owner/repo --json-output
```

## Comment And Merge

```bash
chatgh pr-legacy comment --repo owner/repo --number 123 --body "Looks good"
chatgh pr-legacy merge --repo owner/repo --number 123 --method squash
chatgh pr-legacy merge --repo owner/repo --number 123 --method squash --check
```

## Notes

- Prefer `--body-file` for PR create/edit.
- Keep PR bodies short and structured with `Summary` and `Testing`.
- Use `pr checks` before inspecting individual workflow runs.
- If CI is red, drill down with `run view` and `run logs` instead of guessing from the web UI.
- Before requesting review, update from the target main branch and resolve conflicts locally.
