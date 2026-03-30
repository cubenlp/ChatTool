# test_chattool_client_dispatch_basic

测试统一入口 `chattool` 的 mock 分发链路，覆盖根帮助、`dns` 组装和 `client` 嵌套懒加载。

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
  1. 执行 `chattool --help`，预期输出包含 `dns`、`client`、`skill` 等子命令。
  2. 帮助输出阶段不应触发 `_load_attr`。

参考执行脚本（伪代码）：

```sh
chattool --help
```

## 用例 2：dns 组会挂上 cert-update

- 初始环境准备：
  - patch `_load_attr`，为 `chattool.tools.dns.cli:cli` 返回一个空 group。
  - patch `_load_attr`，为 `chattool.tools.cert.cli:main` 返回一个最小 command。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool dns --help`，预期输出包含 `cert-update`。
  2. `_load_attr` 应按 `dns cli -> cert cli` 的顺序被调用。

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
