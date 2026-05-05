# ChatStyle Migration Inventory

## Scope

This inventory follows the ChatTool ChatStyle decouple PRD. `chattool.interaction.command_schema` remains the command input orchestration layer. `chattool.chatstyle` owns shared output style, prompt primitives, choice helpers, secret masking, setup display helpers, and shared interaction copy.

## Migrated In This Pass

- `src/chattool/chatstyle/constants.py`
  - `-i/-I` help copy.
  - shared back value and checkbox indicators.
  - common no-TTY and missing-argument messages.
- `src/chattool/chatstyle/choice.py`
  - `create_choice()`, `get_separator()`, choice normalization, questionary style.
- `src/chattool/chatstyle/output.py`
  - Rich/click fallback rendering helpers and `get_style()`.
- `src/chattool/chatstyle/prompt.py`
  - `ask_text()`, `ask_path()`, `ask_confirm()`, `ask_select()`, `ask_checkbox()`, `ask_checkbox_with_controls()`.
  - TTY availability and checkbox indicator styling.
- `src/chattool/chatstyle/mask.py`
  - historical `mask_secret()` behavior.
  - current secret display and sensitive prompt helper.
- `src/chattool/chatstyle/setup.py`
  - setup-stage output helpers for start/stage/success/warning/failure/suggested commands/config priority.

## Compatibility Shims

- `src/chattool/interaction/prompt.py` re-exports `chattool.chatstyle.prompt`.
- `src/chattool/interaction/choice.py` re-exports `chattool.chatstyle.choice`.
- `src/chattool/interaction/render.py` re-exports `chattool.chatstyle.output`.
- `src/chattool/interaction/types.py` re-exports `chattool.chatstyle.constants`.
- `src/chattool/interaction/patterns.py` delegates sensitive prompts to `chattool.chatstyle.mask`.
- `src/chattool/utils/basic.py::mask_secret()` delegates to `chattool.chatstyle.mask.mask_secret()`.

## Command Schema Boundary

- `src/chattool/interaction/command_schema.py` still owns:
  - `CommandField`
  - `CommandSchema`
  - `CommandConstraint`
  - `resolve_command_inputs()`
  - value normalization and validation orchestration
- It now uses:
  - `chattool.chatstyle.constants.INTERACTIVE_OPTION_HELP`
  - prompt calls forwarded through `chattool.chatstyle.prompt`

The local forwarding functions keep existing mock paths such as `chattool.interaction.command_schema.ask_text` stable during migration.

## Representative Call-Site Updates

- `src/chattool/setup/elements.py` now uses `INTERACTIVE_OPTION_HELP` for setup command options.
- `src/chattool/tools/pypi/cli.py` now uses `INTERACTIVE_OPTION_HELP` for its manually wired interactive option.
- `src/chattool/tools/cc/cli.py` now uses `INTERACTIVE_OPTION_HELP` for manually wired interactive options.
- `src/chattool/interaction/policy.py` now uses the shared no-TTY message constant.

## Remaining Follow-Up Candidates

- Migrate setup command body output to `chattool.chatstyle.setup` helper calls when touching each setup module.
- Replace local `_mask_secret()` / `_mask_value()` helpers in setup and tool modules with `chattool.chatstyle.mask` where behavior can remain compatible.
- Gradually update direct prompt imports in command modules from `chattool.interaction` to `chattool.chatstyle` only when the module does not depend on command schema or interaction policy.
- Keep `CommandSchema` in `chattool.interaction` unless a later PRD explicitly changes that boundary.
