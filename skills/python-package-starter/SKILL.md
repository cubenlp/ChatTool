---
name: python-package-starter
description: Use `chattool pypi init` or `chatpypi` to scaffold Python packages, including ChatArch templates, then validate with pytest/build/check/probe.
version: 0.2.0
---

# Python Package Starter

Use this skill when creating a Python package with ChatTool's PyPI helpers.

For a generic package, use the `default` template. For a ChatArch / chatxxx CLI package, use the `chatarch` template or switch to `$chatarch-package-dev` for integration guidance.

## Current Command Surface

`chattool pypi` currently provides:

```bash
chattool pypi init
chattool pypi build
chattool pypi check
chattool pypi probe
chattool pypi upload
```

`chatpypi` is a convenience wrapper. When its first argument is not a known pypi subcommand, it dispatches to `chattool pypi init`:

```bash
chatpypi mychat --description "My chat package"
```

## Default Package Quick Start

```bash
chattool pypi init mychat --description "My chat package"
cd mychat
python -m pytest -q
chattool pypi build --project-dir .
chattool pypi check --project-dir .
```

Equivalent wrapper form:

```bash
chatpypi mychat --description "My chat package"
```

The default template creates a minimal `setuptools` + `src/` layout with Python `>=3.9`.

## ChatArch Package Quick Start

Use `chatarch` for a standalone ChatArch CLI package:

```bash
chattool pypi init chatfoo -t chatarch --project-dir ./chatfoo
```

Equivalent wrapper form:

```bash
chatpypi chatfoo -t chatarch --project-dir ./chatfoo
```

The `chatarch` template defaults to Python `>=3.10`, includes `chatstyle` and `chatenv`, and can generate docs and GitHub workflows.

Optional files can be skipped:

```bash
chattool pypi init chatfoo -t chatarch --project-dir ./chatfoo --without-mkdocs --without-workflows
```

## Generated Default Structure

```text
mychat/
├── .gitignore
├── LICENSE
├── README.md
├── pyproject.toml
├── src/
│   └── mychat/
│       └── __init__.py
└── tests/
    ├── conftest.py
    └── test_version.py
```

## Validation

Run the smallest relevant checks before handing off:

```bash
python -m pytest -q
chattool pypi build --project-dir .
chattool pypi check --project-dir .
chattool pypi probe mychat
```

Use `probe` only when checking package-name availability against PyPI is relevant.

## Notes

- Hyphenated package names are converted to underscore module names.
- The generated version comes from `src/<module>/__init__.py`.
- Use `--author` and `--email` when author metadata should be explicit.
- Missing package name auto-enters the interactive wizard in a TTY; `-i` forces prompting and `-I` disables prompting.
- For ChatArch-specific creation/integration, use `$chatarch-package-dev`; for ongoing development after scaffold, use `$chatarch-post-init-dev`.
