# chattool dns cert apply logging

## Case 1: `dns cert apply --log-level DEBUG` should configure updater logger level

- 初始环境准备：
  - patch `chattool.tools.cert.cli.setup_logger` 捕获日志级别。
  - patch `chattool.tools.cert.cli.SSLCertUpdater` 避免真实申请证书。
- 预期过程和结果：
  1. 执行 `chattool dns cert apply --domain example.com --email admin@example.com --log-level DEBUG -I`。
  2. 命令应成功退出。
  3. `setup_logger` 应以 `ssl_cert_updater` 和 `DEBUG` 调用。

```sh
run chattool dns cert apply with --log-level DEBUG
assert logger name and level
```
