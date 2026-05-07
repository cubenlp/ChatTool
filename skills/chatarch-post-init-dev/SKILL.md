---
name: chatarch-post-init-dev
description: Continue development after `chatpypi` or `chattool pypi init -t chatarch` creates a project, keeping chatenv schemas, chatstyle interactive CLI behavior, docs, tests, and changelog aligned.
version: 0.1.0
---

# ChatArch Post-Init Development

Use this skill after a ChatArch / chatxxx project has already been generated with `chatpypi <name> -t chatarch` or `chattool pypi init <name> -t chatarch`.

Goal: turn the scaffold into a maintainable ChatArch package without drifting from the shared `chatstyle` and `chatenv` conventions.

## First Check The Scaffold

From the generated project root:

```bash
python -m pytest -q
python -m mkdocs build --strict
<cli-name> --help
```

Confirm these files exist before expanding the package:

- `AGENTS.md`: agent rules for the new repository.
- `DEVELOP.md`: local development workflow.
- `CHANGELOG.md`: date-based change log.
- `src/<module>/cli.py`: CLI entrypoint.
- `tests/`: generated smoke tests and future behavior tests.
- `docs/` and `mkdocs.yml`: documentation surface when mkdocs is enabled.

## Use ChatStyle For CLI Behavior

Use `chatstyle` directly in standalone ChatArch packages. Do not import `chattool.interaction` from these projects.

Development rules:

- Model recoverable command inputs with `CommandSchema` and `CommandField`.
- Add `@add_interactive_option` to commands that support `-i/-I`.
- Resolve arguments with `resolve_command_inputs()`.
- Do not use Click `required=True` for values that can be asked interactively.
- Keep prompt defaults identical to execution defaults.
- Mask sensitive values in prompts and output.
- Put reusable prompt/render/schema improvements upstream in `chatstyle`, not inside the business package.

Minimal pattern:

```python
from chatstyle import CommandField, CommandSchema, add_interactive_option, resolve_command_inputs

RUN_SCHEMA = CommandSchema(
    name="run",
    fields=(CommandField("target", prompt="target", required=True),),
)

@cli.command()
@click.argument("target", required=False)
@add_interactive_option
def run(target: str | None, interactive: bool | None) -> None:
    inputs = resolve_command_inputs(
        schema=RUN_SCHEMA,
        provided={"target": target},
        interactive=interactive,
        usage="Usage: chatfoo run [TARGET] [-i|-I]",
    )
    ...
```

## Use ChatEnv For Configuration

Keep config schemas in the business package and let `chatenv` discover them through entry points.

Development rules:

- Define provider schemas in `src/<module>/config.py` or a small config package.
- Use `BaseEnvConfig` and `EnvField` from `chatenv`.
- Set `_aliases` for user-facing `-t` selectors.
- Set `_storage_dir` for the directory under `$CHATARCH_HOME/envs/`.
- Mark secrets with `is_sensitive=True`.
- Register the provider under `[project.entry-points."chatenv.configs"]`.
- Do not add a separate env CLI unless there is a strong package-specific reason.

Minimal schema:

```python
from chatenv import BaseEnvConfig, EnvField

class FooConfig(BaseEnvConfig):
    _title = "Foo Configuration"
    _aliases = ["foo", "chatfoo"]
    _storage_dir = "Foo"

    FOO_API_BASE = EnvField("FOO_API_BASE", desc="Foo API base URL")
    FOO_API_KEY = EnvField("FOO_API_KEY", desc="Foo API key", is_sensitive=True)
```

Entry point:

```toml
[project.entry-points."chatenv.configs"]
chatfoo = "chatfoo.config"
```

Validate after installing the package in the active environment:

```bash
chatenv list
chatenv init -t foo
chatenv cat -t foo
chatenv paste --stdin --profile work
```

## Development Loop

For each new behavior:

1. Update CLI/API code under `src/<module>/`.
2. Add or adjust tests under `tests/`.
3. Update `docs/` for user-facing behavior.
4. Update `README.md` if the quickstart changes.
5. Append a dated entry to `CHANGELOG.md`.
6. Run validation before handoff.

Recommended validation:

```bash
python -m pytest -q
python -m mkdocs build --strict
<cli-name> --help
<cli-name> <command> --help
<cli-name> <command> -I
chatenv list
```

Use `-I` checks to ensure non-interactive failure paths do not hang.

## Review Checklist

Before opening or updating a PR, confirm:

- CLI commands expose `-i/-I` where interactive recovery is supported.
- Missing inputs either prompt correctly or fail fast under `-I`.
- No standalone package imports `chattool.interaction`.
- Config schemas are registered through `chatenv.configs`.
- Sensitive env values are masked.
- Tests, docs, README, and `CHANGELOG.md` reflect the change.
- `python -m pytest -q` and `python -m mkdocs build --strict` pass.
