---
name: python-package-starter
description: Use `chattool pypi init` to scaffold a minimal Python package, then validate it with doctor/build/check. Example package name: `mychat`.
---

# Python Package Starter

## Overview

Use `chattool pypi init` to create a minimal `src/`-layout Python package that is ready for `chattool pypi doctor`, `build`, and `check`.

## Quick Start

```bash
chattool pypi init mychat --description "My chat package"
cd mychat
chattool pypi doctor --project-dir .
chattool pypi build --project-dir .
chattool pypi check --project-dir .
```

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
    └── test_version.py
```

## Notes

- `chattool pypi init` defaults to a `setuptools` + `src/` layout.
- The generated version comes from `src/mychat/__init__.py`.
- Hyphenated package names are converted to underscore module names.
- Use `--author` and `--email` if you want author metadata in `pyproject.toml`.

## Suggested Follow-up

```bash
python -m pytest -q
chattool pypi release --project-dir . --dry-run
```
