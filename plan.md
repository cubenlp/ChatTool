## Work Handoff Plan

### Scope
- Add a `chattool gh pr-create` command to create GitHub PRs via token.
- Keep PR creation simple and explicit: repo, base, head, title, body.

### Changes Made
- Added GitHub CLI group:
  - `chattool gh pr-create --repo owner/name --base <branch> --head <branch> --title <title> [--body|--body-file] [--token]`
- Token is read from `GITHUB_ACCESS_TOKEN` if `--token` is not provided.
- Wired new command into main CLI.

### How To Use
1. Export token:
   - `export GITHUB_ACCESS_TOKEN=...`
2. Create PR:
   - `chattool gh pr-create --repo cubenlp/ChatTool --base vibe-master --head rex/network-services-env --title "Make network services check configurable via env" --body-file /path/to/body.md`

### Notes
- Uses PyGithub; if token is missing, command errors clearly.
- No changes to existing gh CLI tooling were present before this.

### Verification
- Not run yet. Suggested:
  - `python -m pytest tests/test_import.py`
  - `chattool gh pr-create ...` with a valid token

