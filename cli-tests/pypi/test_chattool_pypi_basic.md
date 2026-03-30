# test_chattool_pypi_basic

测试 `chattool pypi` 的基础 CLI 链路，覆盖 init、build 与 check。

## 元信息

- 命令：`chattool pypi <command> [args]`
- 目的：验证 PyPI 工具板块已接入主 CLI，并具备最小可用的建包与产物校验能力。
- 标签：`cli`、`e2e`
- 前置条件：本地可执行 Python，临时目录可写。
- 环境准备：创建一个最小 Python 包目录，包含 `pyproject.toml`、`README.md`、`LICENSE`。
- 回滚：删除临时目录。

## 用例 1：init 生成最小 Python 包

- 初始环境准备：
  - 准备一个空目录。
- 相关文件：
  - `<tmp>/mychat/`

预期过程和结果：
  1. 执行 `chattool pypi init mychat --project-dir <tmp>/mychat`，预期生成 `pyproject.toml`、`README.md`、`LICENSE`、`src/mychat/__init__.py`、`tests/conftest.py`、`tests/test_version.py`。
  2. 生成的 `pyproject.toml` 默认写入 `requires-python = ">=3.9"`。
  3. 当缺少包名时，`chattool pypi init` 应直接报错提示需要传入包名或 `--project-dir`，不进入交互式补参。

参考执行脚本（伪代码）：

```sh
chattool pypi init mychat --project-dir /tmp/mychat
chattool pypi init
```

## 用例 2：build/check 验证最小包结构

- 初始环境准备：
  - 已完成 `chattool pypi init mychat`。
- 相关文件：
  - `<tmp>/mychat/pyproject.toml`
  - `<tmp>/mychat/README.md`
  - `<tmp>/mychat/LICENSE`

预期过程和结果：
  1. 执行 `chattool pypi build --project-dir <tmp>/mychat`，预期输出开始日志，并在 `dist/` 下生成构建产物。
  2. 执行 `chattool pypi check --project-dir <tmp>/mychat`，预期输出被检查的构建产物列表。

参考执行脚本（伪代码）：

```sh
chattool pypi build --project-dir /tmp/mychat
chattool pypi check --project-dir /tmp/mychat
```

## 用例 3：生成后可直接运行 pytest

- 初始环境准备：
  - 已完成 `chattool pypi init mychat`。
- 相关文件：
  - `<tmp>/mychat/tests/conftest.py`
  - `<tmp>/mychat/tests/test_version.py`

预期过程和结果：
  1. 进入 `<tmp>/mychat` 后执行 `python -m pytest -q`，预期测试通过，不需要手动设置 `PYTHONPATH`。

参考执行脚本（伪代码）：

```sh
cd /tmp/mychat
python -m pytest -q
```

## 清理 / 回滚

- 删除临时目录。
