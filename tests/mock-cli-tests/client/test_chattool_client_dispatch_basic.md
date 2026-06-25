# test_chattool_client_dispatch_basic

测试统一入口 `chattool` 的 mock 分发链路，覆盖根帮助、已迁移命令缺席和 `client` 嵌套懒加载。

## 元信息

- 命令：`chattool [command]`
- 目的：验证主 CLI 的 lazy group 编排保持稳定，不因子命令增减破坏入口行为。
- 标签：`cli`、`mock`
- 前置条件：无真实依赖；通过 mock `_load_attr` 返回最小 click 命令。
- 环境准备：使用 `CliRunner` 调用统一入口 `chattool`。
- 回滚：无持久化文件写入，无需额外回滚。

## 用例 1：根帮助不触发懒加载

- 初始环境准备：
  - patch `chattool.client.main._load_attr`。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool --help`，预期输出包含 `client`、`skill` 等子命令，且不包含已迁移到 `ChatDNS` 的 `dns`。
  2. 帮助输出阶段不应触发 `_load_attr`。

参考执行脚本（伪代码）：

```sh
chattool --help
```

## 用例 2：dns 已迁移，旧 nested 命令不再懒加载

- 初始环境准备：
  - patch `chattool.client.main._load_attr`，确认不会尝试加载 `chattool.tools.dns.cli:cli`。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool dns --help`，预期返回 `No such command 'dns'`。
  2. `_load_attr` 不应被调用；DNS 实现由独立 `chatdns` CLI 和 package 负责。

参考执行脚本（伪代码）：

```sh
chattool dns --help
```

## 用例 3：client 子命令按需加载

- 初始环境准备：
  - patch `_load_attr`，为 `chattool.client.cert_client:cert_client` 返回一个最小 command。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool client cert --help`，预期输出显示 mock `cert` 命令的帮助文本。
  2. `_load_attr` 仅在解析 `cert` 子命令时被调用。

参考执行脚本（伪代码）：

```sh
chattool client cert --help
```

## 清理 / 回滚

- 无需额外操作。
