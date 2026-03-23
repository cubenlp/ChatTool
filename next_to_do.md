# Next To Do

## Current Branch

- Branch: `rex/feishu-skill`
- Upstream: `origin/rex/feishu-skill`

## Recent Commits

- `65c268f` `feat: harden lark doc and scope flows`
- `c51a4b4` `docs: finalize feishu design migration`
- `02973c5` `docs: clarify cli test policy`
- `1e7bb9f` `docs: reorganize feishu skill topics`
- `b36fe28` `test: add real lark cli coverage`

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
- `chattool lark scopes` now prints a key capability summary and marks likely permission gaps.
- `chattool lark doc append-json` now normalizes unsupported code language style fields before writing blocks.
- Real CLI coverage now also includes the base `lark` command set and the `doc` command set.

## Verified

- Real Feishu CLI tests passed:

```bash
python -m pytest -q \
  cli-tests/lark/test_chattool_lark_basic.py \
  cli-tests/lark/test_chattool_lark_doc_basic.py \
  cli-tests/lark/test_chattool_lark_doc_markdown.py \
  cli-tests/lark-troubleshoot/test_chattool_lark_troubleshoot_basic.py \
  cli-tests/lark-bitable/test_chattool_lark_bitable_basic.py \
  cli-tests/lark-calendar/test_chattool_lark_calendar_basic.py \
  cli-tests/lark-task/test_chattool_lark_task_basic.py \
  cli-tests/lark-im/test_chattool_lark_im_basic.py
```

## Remaining Follow-Up

1. Finish the branch review and update the PR with the current scope.
2. Decide whether `scopes` should stop at terminal diagnostics or also generate/send a permission guidance card.
3. Keep extending `chattool lark <topic> ...` from the topic test docs where needed.

## Known Notes

- `task list` is credential-mode sensitive. Treat failures there as token or scope-mode issues first.
- `calendar primary` falls back to calendar listing because the direct primary endpoint may fail in the current tenant or bot context.
- `im download` must use the `file_key` from the actual message body, not blindly the upload response.
- Local untracked noise should stay ignored:
  - `Auto-claude-code-research-in-sleep/`
