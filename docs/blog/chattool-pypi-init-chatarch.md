# ChatTool 实战｜用 pypi init 创建一个 ChatArch CLI 包

`chattool pypi init` 的目标很简单：把新建 Python CLI 包时反复复制的基础结构一次性生成出来，然后让开发者直接进入业务代码。

这一篇用 `chatfoo` 做一个完整例子，看看 `-t chatarch` 模板到底会生成什么，以及这些文件分别承担什么职责。

---

## 一条命令生成 chatfoo

在任意工作目录里执行：

```bash
chattool pypi init chatfoo \
  -t chatarch \
  --project-dir ./chatfoo \
  --description "ChatArch demo CLI package" \
  --author RexWzh \
  --email 1073853456@qq.com
```

也可以使用短入口：

```bash
chatpypi chatfoo -t chatarch --project-dir ./chatfoo
```

`chatarch` 模板默认会创建 mkdocs 文档和 GitHub workflows；如果只想要最小 CLI 骨架，可以关闭可选文件：

```bash
chattool pypi init chatfoo -t chatarch \
  --without-mkdocs \
  --without-workflows
```

---

## 生成目录

默认模板会生成下面这组文件：

```text
chatfoo/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── deploy.yaml
│       ├── preview.yaml
│       └── publish.yml
├── .gitignore
├── AGENTS.md
├── CHANGELOG.md
├── DEVELOP.md
├── LICENSE
├── README.en.md
├── README.md
├── docs/
│   ├── index.en.md
│   └── index.md
├── mkdocs.yml
├── pyproject.toml
├── src/
│   └── chatfoo/
│       ├── __init__.py
│       └── cli.py
└── tests/
    ├── cli-tests/
    │   └── README.md
    ├── code-tests/
    │   └── README.md
    ├── mock-cli-tests/
    │   └── README.md
    ├── conftest.py
    ├── test_cli.py
    └── test_version.py
```

这不是为了把项目变复杂，而是把 ChatArch 系列项目约定一次写齐：源码、CLI、测试分层、文档、发布 workflow 和 Agent 协作说明都放在固定位置。

---

## pyproject.toml 长什么样？

核心元数据类似这样：

```toml
[project]
name = "chatfoo"
dynamic = ["version"]
description = "ChatArch demo CLI package"
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
dependencies = ["click>=8.0", "chatstyle>=0.1.0", "chatenv>=0.1.1"]
authors = [{name = "RexWzh", email = "1073853456@qq.com"}]

[project.scripts]
chatfoo = "chatfoo.cli:main"

[project.optional-dependencies]
dev = ["build", "pytest", "twine"]
docs = ["mkdocs>=1.4.0", "mkdocs-material>=9.0.0", "mike>=2.0.0"]

[tool.setuptools.dynamic]
version = {attr = "chatfoo.__version__"}
```

这里有三个关键点：

- `chatstyle` 是 CLI 交互规范依赖，负责统一 `-i/-I`、缺参补问和 TUI 输出。
- `chatenv` 是 ChatArch env/profile 底座依赖；模板不内置具体业务 schema，但给 chatxxx 项目预留同一套运行时。
- `version` 来自 `src/chatfoo/__init__.py`，避免在多个位置维护版本号。

---

## CLI 入口长什么样？

模板生成的 `src/chatfoo/cli.py` 是一个最小但符合 ChatArch 规范的命令：

```python
"""CLI entrypoint for chatfoo."""

import click
from chatstyle import (
    CommandField,
    CommandSchema,
    add_interactive_option,
    render_success,
    resolve_command_inputs,
)


HELLO_SCHEMA = CommandSchema(
    name="hello",
    fields=(CommandField("name", prompt="name", required=True),),
)


@click.group()
def main() -> None:
    """chatfoo command line interface."""


@main.command()
@click.argument("name", required=False)
@add_interactive_option
def hello(name: str | None, interactive: bool | None) -> None:
    """Print a greeting with ChatStyle-backed input resolution."""

    values = resolve_command_inputs(
        schema=HELLO_SCHEMA,
        provided={"name": name},
        interactive=interactive,
        usage="Usage: chatfoo hello [NAME]",
    )
    render_success(f"Hello, {values['name']}!")
```

这个例子故意很小，方便看清楚规范：

- 参数可以直接传：`chatfoo hello ChatArch`。
- 缺参时可以进入交互：`chatfoo hello -i`。
- 禁止交互时应快速失败：`chatfoo hello -I`。
- 新命令优先用 `CommandSchema` 描述输入，而不是每个命令自己写一套 prompt 逻辑。

---

## 测试文件做什么？

模板生成两个真正可运行的测试：

```python
# tests/test_version.py
from chatfoo import __version__


def test_version_present():
    assert __version__ == "0.1.0"
```

```python
# tests/test_cli.py
from click.testing import CliRunner

from chatfoo.cli import main


def test_hello_command_accepts_explicit_name():
    result = CliRunner().invoke(main, ["hello", "ChatArch"])

    assert result.exit_code == 0
    assert "Hello, ChatArch!" in result.output
```

同时保留三个 doc-first 测试目录：

- `tests/cli-tests/`：真实 CLI 测试。
- `tests/mock-cli-tests/`：mock/fake CLI 测试。
- `tests/code-tests/`：非 CLI 的代码测试。

后续业务复杂后，可以继续沿用 ChatTool 的测试分层，不需要再重新整理目录。

---

## 文档和 workflow

`mkdocs.yml` 默认只配置两个入口：

```yaml
site_name: chatfoo 文档
site_url: https://OWNER.github.io/REPO
repo_url: https://github.com/OWNER/REPO
theme:
  name: material
  language: zh
nav:
  - 首页: index.md
  - English: index.en.md
```

`.github/workflows/publish.yml` 默认由显式 `v*` tag 或 `workflow_dispatch` 触发，读取 `src/<module>/__init__.py` 里的 `__version__` 并校验 tag 必须等于 `v<__version__>`；当 PyPI 上还没有该版本时构建发行包，并通过 GitHub Trusted Publishing 上传 PyPI：

```yaml
environment: pypi

- name: Check tag matches package version
  if: github.event_name == 'push'
- name: Publish to PyPI
  if: steps.pypi.outputs.exists == 'false'
  uses: pypa/gh-action-pypi-publish@release/v1
```

使用前需要在 PyPI 为该 GitHub 仓库配置 Trusted Publisher，字段应匹配 GitHub owner、repo、workflow 文件名和 `pypi` environment；如果同版本已经存在于 PyPI，workflow 会跳过发布，避免重复上传。

---

## 本地校验

生成后建议先跑下面三步：

```bash
cd chatfoo
python -m pytest -q
python -m build
python -m mkdocs build --strict
```

如果只想校验文档：

```bash
python -m mkdocs serve
```

如果只想检查包元数据和构建物，可以继续用 ChatTool 自己的 PyPI 辅助命令：

```bash
chattool pypi build --project-dir .
chattool pypi check --project-dir .
chattool pypi probe chatfoo
```

---

## 当前 ChatArch 分工

这套模板体现的是当前 ChatArch 的拆分方向：

- `chatstyle`：统一 CLI 交互与输出风格。
- `chatenv`：统一 typed env/profile runtime。
- `chattool`：作为能力集合，同时提供 `pypi init` 这类开发辅助工具。
- `chatxxx` 项目：各自维护自己的业务逻辑、配置 schema 和命令。

所以 `chattool pypi init -t chatarch` 生成的不是一个“ChatTool 插件”，而是一个可独立发布、又能遵守 ChatArch 约定的 Python CLI 包。
