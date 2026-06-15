# test_chattool_serve_local_basic

测试 `chattool serve local` 的 mock 基础链路，覆盖路径解析、统一交互入口和 dry-run 输出。

## 元信息

- 命令：`chattool serve local [TARGET]`
- 目的：验证本地 HTML 静态服务命令可以解析文件/目录目标，并遵循 ChatTool CLI 交互规范。
- 标签：`cli`、`mock`
- 前置条件：无需真实端口监听。
- 环境准备：使用 `CliRunner` 构造临时 HTML 文件和目录。
- 回滚：临时目录由测试框架清理。

## 用例 1：HTML 文件目标

- 初始环境准备：
  - 创建临时文件 `cli-tree.html`。
- 相关文件：
  - `cli-tree.html`

预期过程和结果：
1. 执行 `chattool serve local <file> --host 0.0.0.0 --port 9001 --dry-run`，预期输出文件父目录作为 Root，并输出文件 URL。

参考执行脚本（伪代码）：

```sh
chattool serve local ./cli-tree.html --host 0.0.0.0 --port 9001 --dry-run
```

## 用例 2：目录目标默认 index

- 初始环境准备：
  - 创建临时目录并写入 `index.html`。
- 相关文件：
  - `index.html`

预期过程和结果：
1. 执行 `chattool serve local <dir> --dry-run`，预期打开目录内 `index.html`。

参考执行脚本（伪代码）：

```sh
chattool serve local ./site --dry-run
```

## 用例 3：目录目标指定 HTML

- 初始环境准备：
  - 创建临时目录并写入 `cli-tree.html`。
- 相关文件：
  - `cli-tree.html`

预期过程和结果：
1. 执行 `chattool serve local <dir> --html cli-tree.html --dry-run`，预期 URL 路径为 `/cli-tree.html`。

参考执行脚本（伪代码）：

```sh
chattool serve local ./reports --html cli-tree.html --dry-run
```

## 用例 4：交互补齐目标路径

- 初始环境准备：
  - 当前目录存在 `index.html`。
- 相关文件：
  - `index.html`

预期过程和结果：
1. 执行 `chattool serve local -i --dry-run`，预期通过统一交互机制询问目标路径，默认值为 `.`。

参考执行脚本（伪代码）：

```sh
chattool serve local -i --dry-run
```

## 用例 5：目录缺少 HTML

- 初始环境准备：
  - 创建不含 `index.html` 的临时目录。
- 相关文件：
  - 无

预期过程和结果：
1. 执行 `chattool serve local <dir> --dry-run`，预期报错 `HTML file does not exist`。

参考执行脚本（伪代码）：

```sh
chattool serve local ./empty --dry-run
```

## 清理 / 回滚

- 无需额外操作。
