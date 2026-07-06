# test_chattool_serve_basic

测试 `chattool serve` 的基础链路，覆盖 local/capture/cert/lark/svg2gif 子命令入口。

## 元信息

- 命令：`chattool serve <command> [args]`
- 目的：验证本地服务 CLI 的基础可用性。
- 标签：`cli`
- 前置条件：端口可用。
- 环境准备：确认本地端口未占用。
- 回滚：停止服务进程并清理临时文件。

## 用例 1：帮助信息

- 初始环境准备：
  - 无
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool serve --help`，预期输出子命令列表。

参考执行脚本（伪代码）：

```sh
chattool serve --help
```

## 用例 2：local 静态 HTML 服务

- 初始环境准备：
  - 准备一个本地 HTML 文件，例如 `reports/cli-tree.html`。
- 相关文件：
  - `reports/cli-tree.html`

预期过程和结果：
  1. 在 HTML 所在目录执行 `chattool serve local ./cli-tree.html --host 127.0.0.1 --port 8765`。
  2. 预期命令输出静态服务根目录和可访问 URL。
  3. 浏览器打开 `http://127.0.0.1:8765/cli-tree.html`。

参考执行脚本（伪代码）：

```sh
cd reports
chattool serve local ./cli-tree.html --host 127.0.0.1 --port 8765
```

也支持目录目标：

```sh
chattool serve local ./reports --html cli-tree.html --port 8765
```

## 用例 3：capture 服务

- 初始环境准备：
  - 选定可用端口。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool serve capture --port 8000`，预期服务启动并输出提示。

参考执行脚本（伪代码）：

```sh
chattool serve capture --port 8000
```

## 用例 4：svg2gif 服务

- 初始环境准备：
  - 确保 chromedriver 服务可用并设置 URL。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool serve svg2gif --port 8001`，预期服务启动并可被 `chattool client svg2gif` 调用。

参考执行脚本（伪代码）：

```sh
chattool serve svg2gif --port 8001 --chromedriver-url http://127.0.0.1:9515
```

## 用例 5：cert 服务

- 初始环境准备：
  - 选定可用端口。
- 相关文件：
  - 无

预期过程和结果：
  1. 执行 `chattool serve cert --port 8000`，预期证书服务启动。
  2. Lark bot service 已迁移到 `chatlark serve`，不再由 `chattool serve lark` 提供。

参考执行脚本（伪代码）：

```sh
chattool serve cert --port 8000
```

## 清理 / 回滚

- 停止服务进程。
