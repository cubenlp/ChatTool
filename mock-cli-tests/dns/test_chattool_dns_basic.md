# test_chattool_dns_basic

测试 `chattool dns` 的 mock 基础链路，覆盖 ddns/get/set/cert-update 的命令流程与参数解析。

## 元信息

- 命令：`chattool dns <command> [args]`
- 目的：验证 DNS CLI 编排层的核心命令可用。
- 标签：`cli`、`mock`
- 前置条件：无真实 DNS 服务依赖；通过 mock 隔离 DNS 客户端与 DDNS 执行器。
- 环境准备：使用 `CliRunner` 调用统一入口 `chattool`，通过 patch 验证参数传递。
- 回滚：无持久化文件写入，无需额外回滚。

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
  - patch `DynamicIPUpdater`。
- 相关文件：
  - `dynamic_ip_updater.log`（监控模式）

预期过程和结果：
  1. 执行 `chattool dns ddns test.example.com`，预期解析为 domain=example.com, rr=test。
  2. 执行 `chattool dns ddns -d example.com -r test`，预期与完整域名一致。
  3. 执行 `chattool dns ddns -d example.com -r test --monitor`，预期参数继续传给执行器。

参考执行脚本（伪代码）：

```sh
chattool dns ddns test.example.com
chattool dns ddns -d example.com -r test
chattool dns ddns -d example.com -r test --monitor
```

## 用例 3：set / get 记录

- 初始环境准备：
  - patch `create_dns_client`。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool dns set test.example.com -v 1.2.3.4`，预期客户端收到新增或更新记录请求。
  2. 执行 `chattool dns get test.example.com`，预期客户端收到查询请求。

参考执行脚本（伪代码）：

```sh
chattool dns cert-update -d example.com -e admin@example.com
```

## 清理 / 回滚

- 无需额外操作。
