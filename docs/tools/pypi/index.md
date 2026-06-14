# PyPI 工具

`chattool pypi` 现在只保留最小的一组本地命令：初始化模板、构建、检查、探测，以及一个薄封装的 `upload`。

## 安装

```bash
pip install "chattool[pypi]"
```

如果你只安装了基础版 `chattool`，`build/check/upload` 会提示缺少 `build` 或 `twine`。

## 命令

- `chattool pypi init`：生成一个最小可发布的 `src/` 布局 Python 包骨架
- `chattool pypi build`：执行 `python -m build`
- `chattool pypi check`：执行 `python -m twine check`
- `chattool pypi upload`：执行默认的 `python -m twine upload`
- `chattool pypi probe`：检查包名和版本在 PyPI 或 TestPyPI 是否已存在

## 默认约定

- `--project-dir` 默认为当前目录
- `--dist-dir` 默认为 `<project-dir>/dist`
- `build` 默认同时构建 `sdist` 和 `wheel`
- `init --python` 默认为 default 模板的 `>=3.9`；`chatarch` 模板未显式传 `--python` 时默认 `>=3.10`
- `init --license` 默认为 `MIT`，会写入完整 LICENSE 模板；内置 `MIT`、`Apache-2.0`、`BSD-3-Clause`、`GPL-3.0-only` 和 `Proprietary`
- `upload` 不接管仓库、凭证和交互，直接复用原始 `twine upload` 默认行为
- `init --version` 可直接设置模板初始版本，`probe` 会解析 dynamic version 的真实值

## 使用说明

- init 支持交互式补参：缺少包名且终端可交互时会自动进入向导；`-i` 强制完整向导，`-I` 禁用补问并在缺参时失败。
- `build` 会先打印构建目标目录，便于确认输出位置。
- `upload` 只是 `twine upload` 的薄封装；如需更复杂的上传参数，直接用原始 `twine upload`。

## 常用示例

```bash
chattool pypi init mychat
chattool pypi init mychat --version 0.3.0
chattool pypi build
chattool pypi build --wheel
chattool pypi check
chattool pypi upload
chattool pypi upload --skip-existing
chattool pypi probe --repository pypi
chattool pypi probe mychat --repository pypi
```

## 快速建包

```bash
chattool pypi init mychat --description "My chat package"
cd mychat
python -m pytest -q
chattool pypi build --project-dir .
chattool pypi check --project-dir .
chattool pypi upload --project-dir .
```

默认会生成：

- `pyproject.toml`
- `README.md`
- `LICENSE`
- `.gitignore`
- `src/<module>/__init__.py`
- `tests/conftest.py`
- `tests/test_version.py`

其中 `tests/conftest.py` 会自动把 `src/` 加入导入路径，因此生成后可以直接运行 `python -m pytest -q`。
default 模板生成的 `pyproject.toml` 默认写入 `requires-python = ">=3.9"`；`chatarch` 模板依赖 `chatstyle>=0.1.0` 与 `chatenv>=0.1.1`，默认写入 `requires-python = ">=3.10"`。

`chattool pypi init <name> -t chatarch` 会生成更完整的 CLI 仓库模板：默认中文 README、`README.en.md`、mkdocs 文档入口、`docs/index.en.md`、CI、由 `vX.Y.Z` tag 触发并校验 tag 与 `__version__` 一致后通过 Trusted Publishing 发布 PyPI 的 workflow、mkdocs docs deploy 和 PR preview workflow，并按 ChatArch 规范创建 `src/<module>/cli.py`、`tests/cli-tests`、`tests/mock-cli-tests`、`tests/code-tests`。可用 `--without-mkdocs` 跳过 mkdocs/docs 相关文件，可用 `--without-workflows` 跳过 `.github/workflows/`。
