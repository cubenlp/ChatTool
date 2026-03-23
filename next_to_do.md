# Next To Do

## Current Branch

- Branch: `rex/feishu-skill`
- Upstream: `origin/rex/feishu-skill`

## Recent Commits

- `c51a4b4` `docs: finalize feishu design migration`
- `02973c5` `docs: clarify cli test policy`
- `1e7bb9f` `docs: reorganize feishu skill topics`
- `b36fe28` `test: add real lark cli coverage`
- `cee9dc4` `feat: add lark topic cli foundation`

## Current State

- `chattool lark` now has topic CLI coverage for:
  - `bitable`
  - `calendar`
  - `task`
  - `im`
  - `troubleshoot`
- Feishu skill content is consolidated under a single `skills/feishu/` directory.
- Topic material is flattened into `skills/feishu/*.md` and rewritten around CLI usage.
- Feishu design and user docs were aligned to `docs/design/feishu-cli.md` and `docs/tools/lark/index.md`.
- ChatTool development docs now state that `cli-tests/*.md` is the only long-term maintained test design surface.

## Verified

- Real Feishu CLI tests passed:

```bash
python3 -m pytest -q \
  cli-tests/lark-troubleshoot/test_chattool_lark_troubleshoot_basic.py \
  cli-tests/lark-bitable/test_chattool_lark_bitable_basic.py \
  cli-tests/lark-calendar/test_chattool_lark_calendar_basic.py \
  cli-tests/lark-task/test_chattool_lark_task_basic.py \
  cli-tests/lark-im/test_chattool_lark_im_basic.py
```

## Remaining Follow-Up

1. Finish the branch review and update the PR with the current scope.
2. Keep extending `chattool lark <topic> ...` from the new topic test docs where needed.
3. If scope detection should actively notify users, design a card-based follow-up on top of the current `troubleshoot` markers.

## Known Notes

- `task list` is credential-mode sensitive. Treat failures there as token or scope-mode issues first.
- `calendar primary` falls back to calendar listing because the direct primary endpoint may fail in the current tenant or bot context.
- `im download` must use the `file_key` from the actual message body, not blindly the upload response.
- Local untracked noise should stay ignored:
  - `Auto-claude-code-research-in-sleep/`
