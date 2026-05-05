# 用 ChatTool 创建 Python 包

本文记录如何使用 `chattool pypi init` 快速创建一个可发布的 Python 包，并以 `mychat` 为例说明默认生成的目录结构。

## 最短路径

```bash
chattool pypi init mychat --description "My chat package"
cd mychat
python -m pytest -q
chattool pypi build --project-dir .
chattool pypi check --project-dir .
chattool pypi upload --project-dir .
```

如果你要显式指定作者信息：

```bash
chattool pypi init mychat \
  --author "Rex Wang" \
  --email "rex@example.com" \
  --description "My chat package"
```

`chattool pypi` 现在不再提供交互式补参；缺少必要输入时会直接报错。`upload` 也只是对原始 `twine upload` 的薄封装，如需更复杂的上传参数，直接使用 `twine upload`。

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
- default 模板生成的 `pyproject.toml` 默认写入 `requires-python = ">=3.9"`；`cli-style` 模板依赖 `chatstyle>=0.1.0`，默认写入 `requires-python = ">=3.10"`。
- 版本号来自 `src/mychat/__init__.py` 中的 `__version__`，通过 `tool.setuptools.dynamic` 暴露。
- `tests/conftest.py` 会自动把 `src/` 加入导入路径，保证新项目能直接运行 `python -m pytest -q`。
- 初始 README 已包含 `chattool pypi build/check` 的最短验证命令。
- `LICENSE` 会根据 `--license` 写入模板内容；内置 `MIT`、`Apache-2.0`、`BSD-3-Clause`、`GPL-3.0-only` 和 `Proprietary`。
- `cli-style` 模板会额外生成默认中文文档、`.en.md` 英文副本、mkdocs 配置、docs deploy/preview workflow，以及 `tests/cli-tests`、`tests/mock-cli-tests`、`tests/code-tests`。

## 适用场景

- 新建一个最小可发布的 Python library
- 先搭骨架，再逐步补业务代码
- 在本地快速验证 `pyproject.toml`、构建物和 PyPI 元数据

## 和 skill 的关系

这个流程已经同步沉淀为仓库内的 `python-package-starter` skill。适合后续重复创建类似项目时直接复用。
