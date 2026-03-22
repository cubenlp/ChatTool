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
- `chattool pypi probe`：检查包名和版本在 PyPI 或 TestPyPI 是否已存在
- `chattool pypi publish`：执行 `python -m twine upload`
- `chattool pypi release`：串联 `build -> check -> publish`

## 默认约定

- `--project-dir` 默认为当前目录
- `--dist-dir` 默认为 `<project-dir>/dist`
- 默认目标仓库为 `testpypi`
- 发布到正式 `pypi` 时必须显式 `--yes` 或交互确认
- CLI 认证默认复用 `.pypirc`、`TWINE_USERNAME`、`TWINE_PASSWORD`
- `init --version` 可直接设置模板初始版本，`doctor/probe` 会解析 dynamic version 的真实值

## 交互规范

- 所有 `chattool pypi` 子命令都遵守仓库统一 CLI 规范：缺参自动交互，`-i` 强制完整交互，`-I` 强制非交互。
- 进入交互后，会把当前任务相关的关键参数继续问完，并把真实默认值直接展示在 prompt 中，而不是只补一个参数后静默结束。
- 交互 prompt 统一走 ChatTool 的 TUI 风格，凭证类字段自动隐藏或脱敏。

## 常用示例

```bash
chattool pypi init mychat
chattool pypi init mychat --version 0.3.0
chattool pypi init -i
chattool pypi doctor
chattool pypi build -i
chattool pypi build
chattool pypi check
chattool pypi probe --repository pypi
chattool pypi probe --name mychat --repository pypi
chattool pypi release --dry-run
chattool pypi release --repository testpypi
chattool pypi publish --repository pypi --yes
```

## 快速建包

```bash
chattool pypi init mychat --description "My chat package"
cd mychat
python -m pytest -q
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
- `tests/conftest.py`
- `tests/test_version.py`

其中 `tests/conftest.py` 会自动把 `src/` 加入导入路径，因此生成后可以直接运行 `python -m pytest -q`。

## 认证说明

- 优先使用 `.pypirc`
- 也可以通过 `TWINE_USERNAME` 和 `TWINE_PASSWORD` 提供认证
- 交互模式下可临时输入凭证，不会自动写回配置文件
- `publish/release` 在发现 `.pypirc` 可用时不会先弹凭证输入框

## 交互模式

- `chattool pypi init` 在缺少包名时会进入完整向导，依次提示 `Package name`、`project_dir`、`description`、`requires_python`、`license`、`author`、`email`，并显示默认值。
- `chattool pypi init` 也支持通过 `--version` 或交互中的 `initial_version` 设置模板初始版本。
- `chattool pypi doctor/build/check/publish/release -i` 会先提示当前命令相关的目录、校验或发布参数，再执行实际动作。
- `publish/release` 的确认、仓库和凭证补全也遵循同一套 TUI 规则。
- `-I`：禁止交互；当需要确认或缺少必要输入时直接失败。

这和仓库现有 CLI 约定保持一致，适合本地人工发版与 CI 自动化两种场景。
