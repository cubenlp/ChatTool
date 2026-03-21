# PyPI 工具

`chattool pypi` 用于围绕 Python 包执行本地发版相关操作，覆盖检查、构建、校验和发布计划。

## 安装

```bash
pip install "chattool[pypi]"
```

如果你只安装了基础版 `chattool`，`doctor` 会提示缺少 `build` 或 `twine`。

## 命令

- `chattool pypi doctor`：检查 `pyproject.toml`、`README`、`LICENSE`、`build`、`twine` 与旧的 `dist/` 产物
- `chattool pypi init`：生成一个最小可发布的 `src/` 布局 Python 包骨架
- `chattool pypi build`：执行 `python -m build`
- `chattool pypi check`：执行 `python -m twine check`
- `chattool pypi publish`：执行 `python -m twine upload`
- `chattool pypi release`：串联 `build -> check -> publish`

## 默认约定

- `--project-dir` 默认为当前目录
- `--dist-dir` 默认为 `<project-dir>/dist`
- 默认目标仓库为 `testpypi`
- 发布到正式 `pypi` 时必须显式 `--yes` 或交互确认
- CLI 认证默认复用 `.pypirc`、`TWINE_USERNAME`、`TWINE_PASSWORD`

## 常用示例

```bash
chattool pypi init mychat
chattool pypi doctor
chattool pypi build
chattool pypi check
chattool pypi release --dry-run
chattool pypi release --repository testpypi
chattool pypi publish --repository pypi --yes
```

## 快速建包

```bash
chattool pypi init mychat --description "My chat package"
cd mychat
chattool pypi doctor --project-dir .
chattool pypi build --project-dir .
chattool pypi check --project-dir .
```

默认会生成：

- `pyproject.toml`
- `README.md`
- `LICENSE`
- `.gitignore`
- `src/<module>/__init__.py`
- `tests/test_version.py`

## 认证说明

- 优先使用 `.pypirc`
- 也可以通过 `TWINE_USERNAME` 和 `TWINE_PASSWORD` 提供认证
- 交互模式下可临时输入凭证，不会自动写回配置文件

## 交互模式

- `-i`：强制允许交互确认或凭证输入
- `-I`：禁止交互；当需要确认时直接失败

这和仓库现有 CLI 约定保持一致，适合本地人工发版与 CI 自动化两种场景。
