# test_chattool_pypi_init_interactive

测试 `chattool pypi init` 在交互终端里缺少必要参数时，会自动进入交互补参，而不是直接报错。

## 元信息

- 命令：`chattool pypi init [NAME]`
- 目的：验证 `pypi init` 符合当前 CLI 规范：缺少必要参数时在交互终端自动补问，`-I` 才显式报错。
- 标签：`cli`、`mock`
- 前置条件：无真实 PyPI 依赖。
- 环境准备：使用 `CliRunner`，并通过 monkeypatch 控制交互输入。
- 回滚：删除临时目录。

## 用例 1：缺少包名时自动进入交互

- 初始环境准备：
  - 准备临时目录。
- 相关文件：
  - `<tmp>/demo-pkg/pyproject.toml`

预期过程和结果：
1. 在交互可用条件下执行 `chattool pypi init`，预期不会输出缺少包名的报错。
2. 预期 CLI 会自动补问 `package_name` 和初始化字段，并成功生成项目骨架。

参考执行脚本（伪代码）：

```sh
chattool pypi init
```

## 用例 2：`-I` 明确关闭交互时仍然报错

- 初始环境准备：
  - 无
- 相关文件：
  - 无

预期过程和结果：
1. 执行 `chattool pypi init -I`，预期直接报错提示缺少包名。

参考执行脚本（伪代码）：

```sh
chattool pypi init -I
```

## 用例 3：交互模式支持选择 `cli-style` 模板

- 初始环境准备：
  - 准备临时目录。
- 相关文件：
  - `<tmp>/demo-pkg/DEVELOP.md`
  - `<tmp>/demo-pkg/setup.md`

预期过程和结果：
1. 在交互可用条件下执行 `chattool pypi init`，并把 `template` 选择为 `cli-style`。
2. 预期生成的模板仓库额外包含开发规范、测试约定和初始化说明文件。

参考执行脚本（伪代码）：

```sh
chattool pypi init
select template = cli-style
assert scaffold contains DEVELOP.md and setup.md
```

## 清理 / 回滚

- 删除生成的临时目录。
