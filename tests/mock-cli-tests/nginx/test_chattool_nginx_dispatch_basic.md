# test_chattool_nginx_dispatch_basic

测试 `chattool nginx` 的 mock 基础链路，覆盖模板列表、帮助信息和非交互缺参报错。

## 元信息

- 命令：`chattool nginx [template] [output_file]`
- 目的：验证 `nginx` 板块已接入统一入口，并遵循模板驱动的 CLI 行为。
- 标签：`cli`、`mock`
- 前置条件：无真实 Nginx 依赖。
- 环境准备：使用 `CliRunner` 调用统一入口 `chattool`。
- 回滚：无持久化副作用。

## 用例 1：帮助与模板列表

- 初始环境准备：
  - 无
- 相关文件：
  - 无

预期过程和结果：
1. 执行 `chattool nginx --help`，预期输出 `--list`、`--set` 与参数说明。
2. 执行 `chattool nginx --list`，预期输出 `proxy-pass`、`proxy-pass-https`、`websocket-proxy`、`static-root`、`redirect` 等模板名。

参考执行脚本（伪代码）：

```sh
chattool nginx --help
chattool nginx --list
```

## 用例 2：非交互缺少模板参数

- 初始环境准备：
  - 无
- 相关文件：
  - 无

预期过程和结果：
1. 执行 `chattool nginx -I`，预期直接报错并输出 usage，不进入交互。

参考执行脚本（伪代码）：

```sh
chattool nginx -I
```

## 清理 / 回滚

- 无需额外操作。
