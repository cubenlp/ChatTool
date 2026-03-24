# Next To Do

## Current Branch

- Branch: `rex/feishu-skill`
- Upstream: `origin/rex/feishu-skill`

## Recent Commits

- `6fa4b12` `docs: add feishu document task playbooks`
- `04a4413` `feat: refine feishu cli guidance and skill layout`
- `f2b26ae` `docs: add feishu messaging task playbooks`
- `65c268f` `feat: harden lark doc and scope flows`
- `c51a4b4` `docs: finalize feishu design migration`
- `02973c5` `docs: clarify cli test policy`

## Current State

- `chattool lark` now has topic CLI coverage for:
  - `bitable`
  - `calendar`
  - `task`
  - `im`
  - `troubleshoot`
- Feishu skill content is consolidated under a single `skills/feishu/` directory.
- Root `skills/feishu/` now only keeps `SKILL.md`.
- Topic material is organized into subdirectories:
  - `guide/`
  - `messaging/`
  - `documents/`
  - `calendar/`
  - `task/`
  - `bitable/`
- Feishu design and user docs were aligned to `docs/design/feishu-cli.md` and `docs/tools/lark/index.md`.
- ChatTool development docs now state that `cli-tests/*.md` is the only long-term maintained test design surface.
- `chattool lark scopes` now prints a key capability summary and marks likely permission gaps.
- `chattool lark doc append-json` now normalizes unsupported code language style fields before writing blocks.
- Real CLI coverage now also includes the base `lark` command set and the `doc` command set.
- New document task practice docs now define task-first flows for:
  - create and notify
  - fetch
  - append text / file
  - parse markdown / append json
  - targeted update planning
- Real CLI implementations now cover the supported document task flows:
  - `test_chattool_lark_doc_create_notify_task.py`
  - `test_chattool_lark_doc_fetch_task.py`
  - `test_chattool_lark_doc_append_task.py`
  - `test_chattool_lark_doc_markdown_task.py`

## Verified

- Real Feishu CLI tests passed:

```bash
python -m pytest -q \
  cli-tests/lark/test_chattool_lark_basic.py \
  cli-tests/lark/test_chattool_lark_doc_basic.py \
  cli-tests/lark/test_chattool_lark_doc_markdown.py \
  cli-tests/lark/test_chattool_lark_doc_create_notify_task.py \
  cli-tests/lark/test_chattool_lark_doc_fetch_task.py \
  cli-tests/lark/test_chattool_lark_doc_append_task.py \
  cli-tests/lark/test_chattool_lark_doc_markdown_task.py \
  cli-tests/lark-troubleshoot/test_chattool_lark_troubleshoot_basic.py \
  cli-tests/lark-bitable/test_chattool_lark_bitable_basic.py \
  cli-tests/lark-calendar/test_chattool_lark_calendar_basic.py \
  cli-tests/lark-task/test_chattool_lark_task_basic.py \
  cli-tests/lark-im/test_chattool_lark_im_basic.py
```

## Remaining Follow-Up

1. Decide the first implementation scope for `chattool lark doc update ...`, based on the task doc already written.
2. Continue from documents into the remaining topic task docs and CLI gaps where needed.
3. Keep extending `chattool lark <topic> ...` from the topic task docs where needed.
4. Re-run the real Feishu CLI coverage after the next code-side changes.

## Known Notes

- `task list` is credential-mode sensitive. Treat failures there as token or scope-mode issues first.
- `calendar primary` falls back to calendar listing because the direct primary endpoint may fail in the current tenant or bot context.
- `im download` must use the `file_key` from the actual message body, not blindly the upload response.
- Local untracked noise should stay ignored:
  - `Auto-claude-code-research-in-sleep/`
