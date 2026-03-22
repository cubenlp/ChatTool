# 用 ChatTool 创建 Python 包

本文记录如何使用 `chattool pypi init` 快速创建一个可发布的 Python 包，并以 `mychat` 为例说明默认生成的目录结构。

## 最短路径

```bash
chattool pypi init mychat --description "My chat package"
cd mychat
python -m pytest -q
chattool pypi doctor --project-dir .
chattool pypi build --project-dir .
chattool pypi check --project-dir .
```

如果你希望按统一 CLI 向导逐项确认默认值，可以直接运行：

```bash
chattool pypi init -i
```

它会依次提示：

- `Package name`
- `project_dir`
- `description`
- `requires_python`
- `license`
- `author (optional)`
- `email (optional)`

这些 prompt 中展示的默认值会与最终实际写入的值保持一致。

如果你要显式指定作者信息：

```bash
chattool pypi init mychat \
  --author "Rex Wang" \
  --email "rex@example.com" \
  --description "My chat package"
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
    ├── conftest.py
    └── test_version.py
```

## 关键设计

- 使用标准 `src/` 布局，避免本地路径污染。
- `pyproject.toml` 默认采用 `setuptools.build_meta`。
- 版本号来自 `src/mychat/__init__.py` 中的 `__version__`，通过 `tool.setuptools.dynamic` 暴露。
- `tests/conftest.py` 会自动把 `src/` 加入导入路径，保证新项目能直接运行 `python -m pytest -q`。
- 交互模式遵守全局 CLI 规范：缺参自动进入向导，`-i` 强制完整交互，`-I` 禁止交互。
- 初始 README 已包含 `chattool pypi doctor/build/check` 的最短验证命令。

## 适用场景

- 新建一个最小可发布的 Python library
- 先搭骨架，再逐步补业务代码
- 在本地快速验证 `pyproject.toml`、构建物和 PyPI 元数据

## 和 skill 的关系

这个流程已经同步沉淀为仓库内的 `python-package-starter` skill。适合后续重复创建类似项目时直接复用。
