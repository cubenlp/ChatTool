# test_chattool_dns_basic

测试 `chattool dns` 的 mock 基础链路，覆盖默认交互入口、ddns/get/set/cert-update 的命令流程与参数解析。

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

## 用例 2：根命令默认进入交互选择

- 初始环境准备：
  - patch 交互可用状态和命令选择结果。
- 相关文件：
  - 无

预期过程和结果：
1. 在交互终端执行 `chattool dns`，预期不会只打印帮助，而是先进入命令选择。
2. 当选择 `set` 时，预期继续进入 `set` 命令流程，并补问缺失参数。

参考执行脚本（伪代码）：

```sh
chattool dns
select command = set
input domain / rr / value
```

## 用例 3：ddns 完整域名与分离参数

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

## 用例 4：set / get 缺参时自动补问

- 初始环境准备：
  - patch `create_dns_client` 和交互输入。
- 相关文件：
  - 无

预期过程和结果：
1. 在交互可用条件下执行 `chattool dns set`，预期自动补问 `domain`、`rr`、`value`，而不是先被 Click 的必填参数拦截。
2. 执行 `chattool dns set -I`，预期直接报错，提示缺少必要参数。
3. 在交互可用条件下执行 `chattool dns get`，预期自动补问 `domain` 和 `rr`，随后发起查询。

参考执行脚本（伪代码）：

```sh
chattool dns set
chattool dns set -I
chattool dns get
```

## 清理 / 回滚

- 无需额外操作。
