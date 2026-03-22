---
name: python-package-starter
description: 用 `chattool pypi init` 快速生成最小可发布的 Python 包骨架，并立刻用 doctor/build/check 验证。
version: 0.1.0
---

# Python 包起步（中文）

目标：用 `chattool pypi init` 快速生成一个最小可发布的 Python 包骨架，并立刻用 `doctor/build/check` 验证。

## 最短路径

```bash
chattool pypi init mychat --description "My chat package"
cd mychat
python -m pytest -q
chattool pypi doctor --project-dir .
chattool pypi build --project-dir .
chattool pypi check --project-dir .
```

如果要按 ChatTool 的统一 CLI 交互规范逐项确认默认值，可以直接运行：

```bash
chattool pypi init -i
```

向导会继续提示 `Package name`、`project_dir`、`description`、`requires_python`、`license`、`author`、`email`。

## 默认生成结构

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

## 说明

- 默认采用 `setuptools` 和 `src/` 布局。
- 版本号来自 `src/mychat/__init__.py` 里的 `__version__`。
- `tests/conftest.py` 会把 `src/` 加入导入路径，保证本地直接运行 pytest 可用。
- 包名里如果含 `-`，模块目录会自动转成 `_`。
- 需要写入作者信息时，使用 `--author` 和 `--email`。
- 缺参会自动进入向导，`-i` 强制交互，`-I` 禁止交互。

## 后续建议

```bash
python -m pytest -q
chattool pypi release --project-dir . --dry-run
```
