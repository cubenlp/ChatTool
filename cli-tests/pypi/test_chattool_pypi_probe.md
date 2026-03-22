# test_chattool_pypi_probe

测试 `chattool pypi probe` 的真实链路，验证已存在包名在目标仓库上的占用检查输出。

## 元信息

- 命令：`chattool pypi probe [args]`
- 目的：验证 probe 可通过真实仓库接口发现常见包名已存在，帮助用户在上传前先检查命名冲突。
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
  1. 执行 `chattool pypi probe --name mychat --repository pypi`，预期输出 `repository.project` 检查项。
  2. 对于已存在的 `mychat` 包名，预期 `repository.project` 为 `WARN`，提示该名称已经存在于 `pypi`。
  3. 命令应正常退出，便于用户在修改名称前先做探测。

参考执行脚本（伪代码）：

```sh
chattool pypi probe --name mychat --repository pypi
```
