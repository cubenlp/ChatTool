# test_chattool_pypi_probe

测试 `chattool pypi probe` 的真实链路，验证它按精确项目名检查正式 PyPI，并给出简洁且有价值的结果。

## 元信息

- 命令：`chattool pypi probe [args]`
- 目的：验证 probe 默认面向正式 PyPI，按精确项目名检查，并在命中已有项目时补充少量有用的项目摘要信息。
- 标签：`cli`、`e2e`
- 前置条件：可访问公网；本地可执行 Python。
- 环境准备：无需本地项目目录。
- 回滚：无。

## 用例 1：检查已存在包名

- 初始环境准备：
  - 无。
- 相关文件：
  - 无。

预期过程和结果：
  1. 执行 `chattool pypi probe --name mychat`，预期输出精确项目名检查结果。
  2. 对于已存在的 `mychat` 包名，预期结果直接表明该名称已被占用，不适合作为新包名。
  3. 若命中已有项目，预期输出中可补充少量项目摘要信息，例如最新版本或摘要。

参考执行脚本（伪代码）：

```sh
chattool pypi probe --name mychat
```
