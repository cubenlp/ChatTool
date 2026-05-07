---
name: chatarch-package-dev
description: Create or maintain ChatArch/chatxxx Python CLI packages with `chattool pypi init -t chatarch`, integrating external `chatstyle` and `chatenv` correctly.
version: 0.1.0
---

# ChatArch Package Development

Use this skill when creating or updating a standalone ChatArch / chatxxx Python CLI package.

The package should be independently installable. It is not a ChatTool plugin.

## Start From The Template

```bash
chattool pypi init chatfoo -t chatarch --project-dir ./chatfoo
```

Equivalent wrapper form:

```bash
chatpypi chatfoo -t chatarch --project-dir ./chatfoo
```

Skip optional docs or workflows only when the package does not need them:

```bash
chattool pypi init chatfoo -t chatarch   --project-dir ./chatfoo   --without-mkdocs   --without-workflows
```

## Generated Responsibilities

- `src/<module>/cli.py`: Click CLI using ChatStyle-backed input resolution.
- `src/<module>/__init__.py`: package version and public package marker.
- `tests/`: package tests; add CLI tests as behavior grows.
- `docs/`: maintained documentation when mkdocs is enabled.
- `mkdocs.yml`: docs build config when mkdocs is enabled.
- `.github/workflows/`: CI/docs/publish placeholders when workflows are enabled.
- `AGENTS.md`: agent-facing repository rules.
- `DEVELOP.md`: developer workflow and validation notes.
- `CHANGELOG.md`: date-based change record.

## ChatStyle Integration

Standalone ChatArch packages import `chatstyle` directly. Do not import or copy ChatTool's `chattool.interaction` adapter.

Use `CommandSchema` for recoverable missing inputs:

```python
import click
from chatstyle import CommandField, CommandSchema, add_interactive_option, resolve_command_inputs

HELLO_SCHEMA = CommandSchema(
    name="hello",
    fields=(CommandField("name", prompt="name", required=True),),
)

@click.group()
def cli() -> None:
    pass

@cli.command()
@click.argument("name", required=False)
@add_interactive_option
def hello(name: str | None, interactive: bool | None) -> None:
    inputs = resolve_command_inputs(
        schema=HELLO_SCHEMA,
        provided={"name": name},
        interactive=interactive,
        usage="Usage: chatfoo hello [NAME] [-i|-I]",
    )
    click.echo(f"Hello, {inputs['name']}!")
```

Rules:

- Use `-i` to force the command's interactive flow.
- Use `-I` to disable prompts and fail fast when required inputs are missing.
- Do not use Click `required=True` for inputs that can be recovered interactively.
- Put new reusable prompt/render/schema behavior in `chatstyle`, not in each business package.

## ChatEnv Integration

Use `chatenv` for typed env/profile storage. The business package provides only schema providers.

Minimal `src/chatfoo/config.py`:

```python
from chatenv import BaseEnvConfig, EnvField

class FooConfig(BaseEnvConfig):
    _title = "Foo Configuration"
    _aliases = ["foo", "chatfoo"]
    _storage_dir = "Foo"

    FOO_API_BASE = EnvField("FOO_API_BASE", desc="Foo API base URL")
    FOO_API_KEY = EnvField("FOO_API_KEY", desc="Foo API key", is_sensitive=True)
```

Register it in `pyproject.toml`:

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

## Local Validation

```bash
python -m pytest -q
python -m mkdocs build --strict
chatfoo --help
chatfoo hello ChatArch
chatenv list
chatenv init -t foo
chatenv cat -t foo
```

## Do Not

- Do not copy `chattool.interaction` into standalone packages.
- Do not make `chatenv` hard-code imports for a business package.
- Do not put business env fields into the ChatEnv package itself.
- Do not describe a ChatArch package as a ChatTool plugin.
