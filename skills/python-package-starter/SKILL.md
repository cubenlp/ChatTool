---
name: python-package-starter
description: Use `chattool pypi init` to scaffold a minimal Python package, then validate it with doctor/build/check. Example package name: `mychat`.
version: 0.1.0
---

# Python Package Starter

## Overview

Use `chattool pypi init` to create a minimal `src/`-layout Python package that is ready for `chattool pypi doctor`, `build`, and `check`.

## Quick Start

```bash
chattool pypi init mychat --description "My chat package"
cd mychat
python -m pytest -q
chattool pypi doctor --project-dir .
chattool pypi build --project-dir .
chattool pypi check --project-dir .
```

If you want to review defaults through the standard ChatTool CLI wizard, run:

```bash
chattool pypi init -i
```

The wizard will continue through `Package name`, `project_dir`, `description`, `requires_python`, `license`, `author`, and `email` instead of silently finishing after the first missing field.

## Example Output Structure

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

## Notes

- `chattool pypi init` defaults to a `setuptools` + `src/` layout.
- The generated version comes from `src/mychat/__init__.py`.
- `tests/conftest.py` makes the generated package importable for local pytest runs.
- Hyphenated package names are converted to underscore module names.
- Use `--author` and `--email` if you want author metadata in `pyproject.toml`.
- The interactive flow follows the repo CLI policy: missing required args auto-start the wizard, `-i` forces the full prompt flow, and `-I` disables prompts.

## Suggested Follow-up

```bash
python -m pytest -q
chattool pypi release --project-dir . --dry-run
```
