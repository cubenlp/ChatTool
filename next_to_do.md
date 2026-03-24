# Next To Do

## Current Branch

- Branch: `rex/feishu-skill`
- Upstream: `origin/rex/feishu-skill`

## Recent Commits

- `676a2a8` `test: add real feishu document task coverage`
- `6fa4b12` `docs: add feishu document task playbooks`
- `04a4413` `feat: refine feishu cli guidance and skill layout`
- `f2b26ae` `docs: add feishu messaging task playbooks`
- `65c268f` `feat: harden lark doc and scope flows`

## Current State

- `chattool lark` now has topic CLI coverage for:
  - `bitable`
  - `calendar`
  - `task`
  - `im`
  - `troubleshoot`
- Feishu skill content is consolidated under a single `skills/feishu/` directory.
- Root `skills/feishu/` only keeps `SKILL.md`.
- Skill topics are organized into:
  - `guide/`
  - `messaging/`
  - `documents/`
  - `calendar/`
  - `task/`
  - `bitable/`
- Feishu CLI tests are being reorganized to mirror skill topics under `cli-tests/lark/<topic>/`.
- Real CLI implementations now cover the supported document task flows:
  - `test_chattool_lark_doc_create_notify_task.py`
  - `test_chattool_lark_doc_fetch_task.py`
  - `test_chattool_lark_doc_append_task.py`
  - `test_chattool_lark_doc_markdown_task.py`

## Verified

- Real Feishu CLI tests passed before the directory move:

```bash
python -m pytest -q \
  cli-tests/lark/guide/test_chattool_lark_basic.py \
  cli-tests/lark/documents/test_chattool_lark_doc_basic.py \
  cli-tests/lark/documents/test_chattool_lark_doc_markdown.py \
  cli-tests/lark/documents/test_chattool_lark_doc_create_notify_task.py \
  cli-tests/lark/documents/test_chattool_lark_doc_fetch_task.py \
  cli-tests/lark/documents/test_chattool_lark_doc_append_task.py \
  cli-tests/lark/documents/test_chattool_lark_doc_markdown_task.py \
  cli-tests/lark/troubleshoot/test_chattool_lark_troubleshoot_basic.py \
  cli-tests/lark/bitable/test_chattool_lark_bitable_basic.py \
  cli-tests/lark/calendar/test_chattool_lark_calendar_basic.py \
  cli-tests/lark/task/test_chattool_lark_task_basic.py \
  cli-tests/lark/im/test_chattool_lark_im_basic.py
```

## Remaining Follow-Up

1. Finish updating all Feishu skill/doc references to the new `cli-tests/lark/<topic>/` layout.
2. Re-run the Feishu real CLI coverage using the new test paths.
3. Decide the first implementation scope for `chattool lark doc update ...`, based on the task doc already written.
4. Continue from documents into the remaining topic task docs and CLI gaps where needed.

## Known Notes

- `task list` is credential-mode sensitive. Treat failures there as token or scope-mode issues first.
- `calendar primary` falls back to calendar listing because the direct primary endpoint may fail in the current tenant or bot context.
- `im download` must use the `file_key` from the actual message body, not blindly the upload response.
- Local untracked noise should stay ignored:
  - `Auto-claude-code-research-in-sleep/`
