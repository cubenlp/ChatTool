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
- `upload` 不接管仓库、凭证和交互，直接复用原始 `twine upload` 默认行为
- `init --version` 可直接设置模板初始版本，`probe` 会解析 dynamic version 的真实值

## 使用说明

- 这组命令不再提供交互式补参；缺少必要输入时直接报错。
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
chattool pypi probe --name mychat --repository pypi
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
