# test_chattool_pypi_basic

测试 `chattool pypi` 的基础 CLI 链路，覆盖 doctor 与 release --dry-run。

## 元信息

- 命令：`chattool pypi <command> [args]`
- 目的：验证 PyPI 工具板块已接入主 CLI，并具备最小可用的包检查与发布计划输出能力。
- 标签：`cli`、`e2e`
- 前置条件：本地可执行 Python，临时目录可写。
- 环境准备：创建一个最小 Python 包目录，包含 `pyproject.toml`、`README.md`、`LICENSE`。
- 回滚：删除临时目录。

## 用例 1：doctor 检查最小包结构

- 初始环境准备：
  - 创建最小包目录。
- 相关文件：
  - `<tmp>/pkg/pyproject.toml`
  - `<tmp>/pkg/README.md`
  - `<tmp>/pkg/LICENSE`

预期过程和结果：
  1. 执行 `chattool pypi doctor --project-dir <tmp>/pkg`，预期输出 pyproject、readme、license 等检查项。

参考执行脚本（伪代码）：

```sh
chattool pypi doctor --project-dir /tmp/pkg
```

## 用例 2：release dry-run 输出发版计划

- 初始环境准备：
  - 复用同一个最小包目录。
- 相关文件：
  - `<tmp>/pkg/pyproject.toml`

预期过程和结果：
  1. 执行 `chattool pypi release --project-dir <tmp>/pkg --dry-run`，预期输出 build/check/publish 顺序计划，但不真正执行构建和上传。

参考执行脚本（伪代码）：

```sh
chattool pypi release --project-dir /tmp/pkg --dry-run
```

## 清理 / 回滚

- 删除临时目录。
