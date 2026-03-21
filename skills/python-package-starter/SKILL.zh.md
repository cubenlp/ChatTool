# Python 包起步（中文）

目标：用 `chattool pypi init` 快速生成一个最小可发布的 Python 包骨架，并立刻用 `doctor/build/check` 验证。

## 最短路径

```bash
chattool pypi init mychat --description "My chat package"
cd mychat
chattool pypi doctor --project-dir .
chattool pypi build --project-dir .
chattool pypi check --project-dir .
```

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
    └── test_version.py
```

## 说明

- 默认采用 `setuptools` 和 `src/` 布局。
- 版本号来自 `src/mychat/__init__.py` 里的 `__version__`。
- 包名里如果含 `-`，模块目录会自动转成 `_`。
- 需要写入作者信息时，使用 `--author` 和 `--email`。

## 后续建议

```bash
python -m pytest -q
chattool pypi release --project-dir . --dry-run
```
