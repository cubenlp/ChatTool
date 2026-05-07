---
name: python-package-starter
description: 使用 `chattool pypi init` 或 `chatpypi` 创建 Python 包，包括 ChatArch 模板，并用 pytest/build/check/probe 验证。
version: 0.2.0
---

# Python 包起步

当需要用 ChatTool 的 PyPI helper 创建 Python 包时使用这个 skill。

普通 Python 包使用 `default` 模板。ChatArch / chatxxx CLI 包使用 `chatarch` 模板；如果还要集成 `chatstyle` / `chatenv`，继续使用 `$chatarch-package-dev`。

## 当前命令面

`chattool pypi` 当前提供：

```bash
chattool pypi init
chattool pypi build
chattool pypi check
chattool pypi probe
chattool pypi upload
```

`chatpypi` 是便捷入口。如果第一个参数不是已知 pypi 子命令，会转发到 `chattool pypi init`：

```bash
chatpypi mychat --description "My chat package"
```

## 默认包最短路径

```bash
chattool pypi init mychat --description "My chat package"
cd mychat
python -m pytest -q
chattool pypi build --project-dir .
chattool pypi check --project-dir .
```

等价 wrapper 写法：

```bash
chatpypi mychat --description "My chat package"
```

默认模板会创建最小 `setuptools` + `src/` 布局，Python 下限为 `>=3.9`。

## ChatArch 包最短路径

独立 ChatArch CLI 包使用 `chatarch` 模板：

```bash
chattool pypi init chatfoo -t chatarch --project-dir ./chatfoo
```

等价 wrapper 写法：

```bash
chatpypi chatfoo -t chatarch --project-dir ./chatfoo
```

`chatarch` 模板默认 Python 下限为 `>=3.10`，包含 `chatstyle` 与 `chatenv` 依赖，并可生成 docs 与 GitHub workflows。

如需跳过可选文件：

```bash
chattool pypi init chatfoo -t chatarch --project-dir ./chatfoo --without-mkdocs --without-workflows
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

## 验证

交付前优先跑最小相关检查：

```bash
python -m pytest -q
chattool pypi build --project-dir .
chattool pypi check --project-dir .
chattool pypi probe mychat
```

只有需要检查 PyPI 包名可用性时才运行 `probe`。

## 说明

- 包名包含 `-` 时，模块目录会自动转为 `_`。
- 版本号来自 `src/<module>/__init__.py`。
- 需要明确作者信息时使用 `--author` 和 `--email`。
- TTY 中缺少包名会自动进入向导；`-i` 强制交互，`-I` 禁止交互。
- ChatArch 专属的创建/集成说明见 `$chatarch-package-dev`；scaffold 之后的持续开发规范见 `$chatarch-post-init-dev`。
