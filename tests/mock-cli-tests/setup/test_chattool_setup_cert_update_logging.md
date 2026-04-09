# chattool dns cert-update logging

## Case 1: `dns cert-update --log-level DEBUG` should configure updater logger level

### 初始环境准备

- mock 掉证书更新器执行，仅校验 logger 初始化参数。

### 预期过程和结果

- 执行 `chattool dns cert-update --domains example.com --email admin@example.com --log-level DEBUG -I`。
- 命令应接受 `-l/--log-level`。
- `setup_logger()` 应按 `DEBUG` 级别初始化 logger。

### 参考执行脚本（伪代码）

```sh
stub setup_logger and updater.run_once
run chattool dns cert-update with --log-level DEBUG
assert logger is configured with DEBUG
```
