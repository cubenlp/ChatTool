# test_chattool_dns_basic

测试 `chattool dns` 的基础链路，覆盖 ddns/get/set/cert-update 的命令流程与参数解析。

## 元信息

- 命令：`chattool dns <command> [args]`
- 目的：验证 DNS CLI 的核心命令可用。
- 标签：`cli`
- 前置条件：具备 DNS 服务凭证与测试域名。
- 环境准备：配置 DNS 凭证与测试域名。
- 回滚：删除测试产生的 DNS 记录。

## 用例 1：帮助信息

- 初始环境准备：
  - 无
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool dns get --help`，预期输出命令说明。
  2. 执行 `chattool dns ddns --help`，预期输出命令说明。
  3. 执行 `chattool dns cert-update --help`，预期输出命令说明。

参考执行脚本（伪代码）：

```sh
chattool dns get --help
chattool dns ddns --help
chattool dns cert-update --help
```

## 用例 2：ddns 完整域名与分离参数

- 初始环境准备：
  - 准备测试域名与子域。
- 相关文件：
  - `dynamic_ip_updater.log`（监控模式）

预期过程和结果：
  1. 执行 `chattool dns ddns test.example.com`，预期解析为 domain=example.com, rr=test。
  2. 执行 `chattool dns ddns -d example.com -r test`，预期与完整域名一致。
  3. 执行 `chattool dns ddns -d example.com -r test --monitor`，预期进入持续监控模式。

参考执行脚本（伪代码）：

```sh
chattool dns ddns test.example.com
chattool dns ddns -d example.com -r test
chattool dns ddns -d example.com -r test --monitor
```

## 用例 3：set / get 记录

- 初始环境准备：
  - 准备测试域名与记录值。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool dns set test.example.com -v 1.2.3.4`，预期记录被创建或更新。
  2. 执行 `chattool dns get test.example.com`，预期返回记录信息。

参考执行脚本（伪代码）：

```sh
chattool dns set test.example.com -v 1.2.3.4
chattool dns get test.example.com
```

## 用例 4：证书更新

- 初始环境准备：
  - 配置 DNS 凭证与可用域名。
- 相关文件：
  - `<cert-dir>/<domain>/fullchain.pem`
  - `<cert-dir>/<domain>/privkey.pem`

预期过程和结果：
  1. 执行 `chattool dns cert-update -d example.com -e admin@example.com`，预期证书文件生成。

参考执行脚本（伪代码）：

```sh
chattool dns cert-update -d example.com -e admin@example.com
```

## 清理 / 回滚

- 删除测试记录或还原为原始值。
