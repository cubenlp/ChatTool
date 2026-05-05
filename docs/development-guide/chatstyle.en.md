# ChatStyle

The external `chatstyle` package is the canonical ChatArch CLI interaction runtime. ChatTool no longer keeps a local `chattool.chatstyle` style layer; shared prompt, choice, render, mask, and schema runtime all come from external `chatstyle`. ChatTool keeps only `chattool.interaction` as command-side adapters for existing policy, usage, and test patch points. Business commands should describe fields, arguments, and behavior; they should not reimplement TTY checks, prompt backends, masking rules, or `-i/-I` help text.

Chinese version: [chatstyle.md](chatstyle.md).

## Module Boundary

- `chatstyle.render`
  - Headings, notes, Rich/click fallback rendering, and common display helpers.
- `chatstyle.tui`
  - `ask_text()`, `ask_path()`, `ask_confirm()`, `ask_select()`, `ask_checkbox()`, `ask_checkbox_with_controls()`, and TTY availability.
- `chatstyle.tui.choice`
  - `create_choice()`, `get_separator()`, choice normalization, and questionary style.
- `chatstyle.security`
  - `mask_secret()`, current-secret display, and sensitive prompt behavior where Enter keeps the current value.
- `chatstyle.render` flow helpers
  - Stage display helpers for start, stage, success, warning, failure, suggested commands, and config priority. Names use `render_*` to avoid confusion with ChatTool's `setup` command group.
- `chatstyle.core`
  - Shared constants such as `BACK_VALUE`, checkbox indicators, and `INTERACTIVE_OPTION_HELP`.
- `chattool.interaction`
  - ChatTool command-side adapter package entrypoint that continues exporting `ask_*`, `create_choice()`, `CommandSchema`, and `add_interactive_option()`. Pure shared capabilities are re-exported directly from external `chatstyle`; only `command_schema` / `policy` keep ChatTool-side parameter-source, usage, and test patch-point logic.

## Command Schema

The canonical `CommandSchema` implementation lives in external `chatstyle.input`. ChatTool commands should keep importing from `chattool.interaction.command_schema` so legacy mock paths and ChatTool policy adapters remain stable:

- `CommandField`
- `CommandSchema`
- `CommandConstraint`
- `resolve_command_inputs()`
- `add_interactive_option()`

Use `CommandSchema` for new commands with recoverable missing arguments. Do not copy another schema runtime into ChatTool.

## Prompt Usage

New shared prompt behavior belongs in external `chatstyle`. ChatTool commands should import from `chattool.interaction` when they need project policy or existing test patch points; new shared behavior should not be added back to ChatTool locally.

Prefer schema-driven prompting for command arguments. Use direct prompt primitives only for flows that are inherently page-like or wizard-like, such as category selection, setup mode selection, or checkbox selection.

Sensitive fields should use password input and masked current-value display. Prefer `chatstyle.prompt_sensitive_value()` when Enter should keep the existing value; ChatTool commands can use the matching pattern helper from `chattool.interaction` when they need project policy.

## Interactive Policy

Use `@add_interactive_option` from `chattool.interaction.command_schema` for normal commands. It wires:

```text
--interactive/--no-interactive
-i/-I
```

The help text comes from external `chatstyle.INTERACTIVE_OPTION_HELP`. Commands that declare Click options directly should import `chatstyle.INTERACTIVE_OPTION_HELP`; ordinary commands should prefer `chattool.interaction.add_interactive_option()`.

Semantics:

- Missing required values may auto-prompt when a TTY is available.
- `-i` forces the current command's interactive flow.
- `-I` fully disables interactive prompting.
- Forced interactive mode without TTY must fail with a shared human-readable message.

## Output Style

Use external `chatstyle.render` for reusable display patterns. Business modules may still print domain-specific results directly, but common headings, notes, summaries, and error display should not be reinvented per command.

When Rich is unavailable, helpers must fall back to plain Click output.

## Setup Style

Setup commands should expose observable stages:

- Start
- Dependency detection
- Install or external operation
- Config write
- Validation
- Completion or failure reason

If a setup flow requires sudo, it must provide an explicit `--sudo` switch. Without `--sudo`, print suggested commands instead of executing them. Use external `chatstyle.render_suggested_commands()` for this display.

When a setup command resolves values from multiple sources, document and show the priority consistently:

```text
explicit args > -e/--env > tool default config > system env > ChatTool .env > default
```

## Migration Boundary

The local `chattool.chatstyle` module has been removed. The `chattool.interaction` package entrypoint remains as the ChatTool command-side adapter over external `chatstyle`; pure forwarding submodules such as prompt, choice, render, and constants are no longer kept locally. New reusable style behavior must be added to the external ChatStyle project first; ChatTool should add adapters only when it needs project policy, usage, or test patch points.

## CLI Test Expectations

CLI behavior remains doc-first:

- Real CLI tests live in `tests/cli-tests`.
- Mock CLI orchestration tests live in `tests/mock-cli-tests`.
- Mock paths that patch `chattool.interaction.command_schema.ask_text` remain valid during migration.

When adding or changing CLI interactions, verify:

- Missing arguments enter interactive only when allowed.
- `-i` and `-I` keep their documented behavior.
- Default values shown in prompts match actual execution.
- Sensitive values are masked in display and hidden during input.
- Non-TTY errors are readable and actionable.
